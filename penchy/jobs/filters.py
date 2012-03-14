"""
This module provides filters.

Inputs are fed to filters via keywords in the ``run`` method.
Outputs are available via the ``out`` attribute.

 .. moduleauthor:: Michael Markert <markert.michael@googlemail.com>
 .. moduleauthor:: Pascal Wittmann <mail@pascal-wittmann.de>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
from __future__ import division

import json
import logging
import os
import re
import shutil
import math
import csv
import operator
from pprint import pprint

from penchy import __version__
from penchy.compat import str, path, unicode, try_unicode, write
from penchy.jobs.elements import Filter, SystemFilter
from penchy.jobs.typecheck import Types, TypeCheckError
import penchy.util as util
import penchy.statistics as stats
from penchy.deploy import Deploy


log = logging.getLogger(__name__)


class WrongInputError(Exception):
    """
    Filter received input it was not expecting and cannot process.
    """
    pass


class Value(object):
    """
    Represents a value in the context of the :class:`~penchy.jobs.filters.Merge`
    filter. It is used to distinguish direct values from filter inputs.
    """
    def __init__(self, value):
        """
        :param value: the value
        :type value: object
        """
        self.value = value


class Tamiflex(Filter):
    """
    A filter for the reflection log file of the tamiflex
    play-out-agent.

    Inputs:

    - ``reflection_log``: Path to the reflection log file

    Outputs:

    - ``kind``: Kind of reflection call
    - ``name``: qualified name of instantiated class or the
                signature of the called method/constructor
    - ``parent_name``: the fully qualified name of the method
                       that contains the reflective call
    - ``line``: the line number at which the reflective call
                took place (maybe empty)
    - ``optional``: optionally additional information, such as
                    the accessibility status of the member in question
    """
    inputs = Types(('reflection_log', list, path))
    outputs = Types(('kind', list, list, str),
                    ('name', list, list, str),
                    ('parent_name', list, list, str),
                    ('line', list, list, str),
                    ('optional', list, list, str))

    def _run(self, **kwargs):
        files = kwargs['reflection_log']

        for f in files:
            if not os.path.getsize(f):
                raise WrongInputError("The reflection log is empty")
            with open(f) as fobj:
                data = {'kind': [], 'name': [], 'parent_name': [],
                        'line': [], 'optional': []}
                tamiflex_reader = csv.reader(fobj, delimiter=';')
                for row in tamiflex_reader:
                    if len(row) != len(data):
                        raise WrongInputError("The reflection log is malformed: {0}".format(row))
                    for value, name in zip(row, data):
                        data[name].append(value)

                for key, val in data.items():
                    self.out[key].append(val)


class HProf(Filter):
    """
    A filter that abstracts the hprof output and aims
    to make it easy creating new hprof filters.

    It is nessasarry, that the ``data_re`` regular expression
    supports ``groupdict`` and that the resulting keys
    match with the keys in ``outputs``.
    """
    inputs = Types(('hprof', list, path))

    def __init__(self, outputs, start_marker, end_marker, skip, data_re, start_re=None):
        """
        :param outputs: outputs of the filter
        :type outputs: :class:`~penchy.jobs.typecheck.Types`
        :param start_marker: the string with which the data segment starts
        :type start_marker: string
        :param end_marker: the string with which the data segment ends
        :type end_maker: string
        :param skip: lines to skip before the actual data begin
        :type skip: integer
        :param data_re: regular expression to match one data line
        :type data_re: ``re``
        :param start_re: regular expression to extract information out of the first line
        :type start_re: ``re``
        """
        super(HProf, self).__init__()
        self.outputs = outputs
        self.start_marker = start_marker
        self.end_marker = end_marker
        self.start_re = start_re
        self.data_re = data_re
        self.skip = skip

        # Names of 1 dimensional outputs
        self.names1d = [k for k, d in self.outputs.descriptions.items() if len(d) == 2]
        if len(self.names1d) > 1:
            raise ValueError("The current implementation only allows one 1 dimensional output")

        # Names of 2 dimensional outputs
        self.names2d = [k for k, d in self.outputs.descriptions.items() if len(d) == 3]

    def _run(self, **kwargs):
        files = kwargs['hprof']

        for f in files:
            data = dict((name, []) for name in self.names2d)

            with open(f) as fobj:
                for line in fobj:
                    if line.startswith(self.start_marker):
                        break
                # We did not break, i.e. no begin marker was found
                else:
                    raise WrongInputError("Marker {0} not found.".format(self.start_marker))

                # Extract information from the start marker
                if self.start_re is not None:
                    s = self.start_re.search(line)
                    if s is None:
                        log.error('Received invalid input:\n{0}'.format(line))
                        raise WrongInputError('Received invalid input.')
                    start_value = s.groups()[0]
                    name = self.names1d[0]
                    type_ = self.outputs.descriptions[name][-1]
                    self.out[name].append(type_(start_value))

                # Jump over the heading
                for _ in range(self.skip):
                    next(fobj)

                for line in fobj:
                    if line.startswith(self.end_marker):
                        break
                    m = self.data_re.match(line)
                    if m is None:
                        log.error('Received invalid input:\n{0}'.format(line))
                        raise WrongInputError('Received invalid input.')
                    result = self.data_re.match(line).groupdict()

                    # Cast and save the extracted values
                    for name in self.names2d:
                        type_ = self.outputs.descriptions[name][-1]
                        data[name].append(type_(result[name]))

                # We did not break, i.e. no end marker was found
                else:
                    raise WrongInputError("Marker {0} not found.".format(self.end_marker))

                for key, val in data.items():
                    self.out[key].append(val)


class HProfCpuTimes(HProf):
    """
    Filters cpu=times output of hprof

    Inputs:

    - ``hprof``: Path to the hprof output file

    Outputs:

    - ``total``: Total execution time (ms)
    - ``rank``: Rank of the method
    - ``self``: Thread time (%)
    - ``accum``: Thread time (%)
    - ``count``: How often this method was entered
    - ``trace``: Stack trace number
    - ``method``: Absolute method name
    """
    outputs = Types(('total', list, int),
                    ('rank', list, list, int),
                    ('selftime', list, list, float),
                    ('accum', list, list, float),
                    ('count', list, list, int),
                    ('trace', list, list, int),
                    ('method', list, list, str))

    _TOTAL_RE = re.compile('total = (\d+)')
    _DATA_RE = re.compile("""
       \s+(?P<rank>\d+)
       \s+(?P<selftime>\d+\.\d{2})%
       \s+(?P<accum>\d+\.\d{2})%
       \s+(?P<count>\d+)
       \s+(?P<trace>\d+)
       \s+(?P<method>[^\s]+)
       """, re.VERBOSE)

    def __init__(self):
        super(HProfCpuTimes, self).__init__(outputs=self.outputs,
                                            start_marker='CPU TIME (ms) BEGIN',
                                            end_marker='CPU TIME (ms) END',
                                            skip=1,
                                            data_re=HProfCpuTimes._DATA_RE,
                                            start_re=HProfCpuTimes._TOTAL_RE)


class HProfCpuSamples(HProf):
    """
    Filters cpu=samples output of hprof

    Inputs:

    - ``hprof``: Path to the hprof output file

    Outputs:

    - ``total``: Total samples
    - ``rank``: Rank of the method
    - ``self``: Thread time (%)
    - ``accum``: Thread time (%)
    - ``count``: How often a stack trace was active
    - ``trace``: Stack trace number
    - ``method``: Absolute method name
    """
    outputs = Types(('total', list, int),
                    ('rank', list, list, int),
                    ('selftime', list, list, float),
                    ('accum', list, list, float),
                    ('count', list, list, int),
                    ('trace', list, list, int),
                    ('method', list, list, str))

    _TOTAL_RE = re.compile('total = (\d+)')
    _DATA_RE = re.compile("""
       \s+(?P<rank>\d+)
       \s+(?P<selftime>\d+\.\d{2})%
       \s+(?P<accum>\d+\.\d{2})%
       \s+(?P<count>\d+)
       \s+(?P<trace>\d+)
       \s+(?P<method>[^\s]+)
       """, re.VERBOSE)

    def __init__(self):
        super(HProfCpuSamples, self).__init__(outputs=self.outputs,
                                            start_marker='CPU SAMPLE (ms) BEGIN',
                                            end_marker='CPU SAMPLE (ms) END',
                                            skip=1,
                                            data_re=HProfCpuSamples._DATA_RE,
                                            start_re=HProfCpuSamples._TOTAL_RE)


class HProfHeapSites(HProf):
    """
    Filters heap=sites output of hprof

    Inputs:

    - ``hprof``: Path to the hprof output file

    Outputs:

    - ``rank``: Rank of the method
    - ``self``: space at a particular site (%)
    - ``accum``: total space at a particular site (%)
    - ``live_bytes``: TODO
    - ``live_objs``: TODO
    - ``alloc_bytes``: TODO
    - ``alloc_objs``: TODO
    - ``trace``: TODO
    - ``class``: class name
    """
    outputs = Types(('rank', list, list, int),
                    ('self', list, list, float),
                    ('accum', list, list, float),
                    ('live_bytes', list, list, int),
                    ('live_objs', list, list, int),
                    ('alloc_bytes', list, list, int),
                    ('alloc_objs', list, list, int),
                    ('trace', list, list, int),
                    ('class', list, list, str))

    _DATA_RE = re.compile("""
       \s+(?P<rank>\d+)
       \s+(?P<self>\d+\.\d{2})%
       \s+(?P<accum>\d+\.\d{2})%
       \s+(?P<live_bytes>\d+)
       \s+(?P<live_objs>\d+)
       \s+(?P<alloc_bytes>\d+)
       \s+(?P<alloc_objs>\d+)
       \s+(?P<class>[^\s]+)
       """, re.VERBOSE)

    def __init__(self):
        super(HProfHeapSites, self).__init__(outputs=self.outputs,
                                            start_marker='SITES BEGIN',
                                            end_marker='SITES END',
                                            skip=2,
                                            data_re=HProfHeapSites._DATA_RE)


class DacapoHarness(Filter):
    """
    Filters output of a DaCapo Harness.

    Inputs:

    - ``stderr``:  List of Paths to stderror output files

    Outputs:

    - ``failures``: failure count per invocation
    - ``times``: execution time per itertion per invocation
    - ``valid``: flag that indicates if execution was valid
    """
    inputs = Types(('stderr', list, path))

    outputs = Types(('failures', list, int, int),
                    ('times', list, list, int),
                    ('valid', list, bool))

    _TIME_RE = re.compile(
        r"""
        (?:completed\ warmup\ \d+|        # for iterations
        (?P<success>FAILED|PASSED))       # check if run failed or passed
        \ in\ (?P<time>\d+)\ msec         # time of execution
        """, re.VERBOSE)

    _VALIDITY_RE = re.compile(r'^\n?={5} DaCapo .*?={5}\n={5} DaCapo')

    def _run(self, **kwargs):
        stderror = kwargs['stderr']

        for f in stderror:
            failures = 0
            times = []
            with open(f) as fobj:
                buf = fobj.read()

            if not self._VALIDITY_RE.search(buf):
                log.error('Received invalid input:\n{0}'.format(buf))
                raise WrongInputError('Received invalid input')

            for match in DacapoHarness._TIME_RE.finditer(buf):
                success, time = match.groups()
                if success is not None and success == 'FAILED':
                    failures += 1
                times.append(int(time))

            self.out['failures'].append(failures)
            self.out['times'].append(times)
            self.out['valid'].append(failures == 0)


class Send(SystemFilter):
    """
    Sends all data fed to it to the server.

    Inputs:

    - ``:environment:``: see :meth:`Job._build_environment`
    """
    inputs = Types()

    def _run(self, **kwargs):
        send = kwargs.pop(':environment:')['send']
        send(kwargs)


class Receive(SystemFilter):
    """
    Makes received data available for the serverside pipeline.

    Inputs:

    - ``:environment:``: see :meth:`Job._build_environment`

    Outputs:

    - ``results``: dict that maps :class:`SystemComposition` to their results.
    """
    inputs = Types((':environment:', dict))
    outputs = Types(('results', dict))

    def _run(self, **kwargs):
        receive = kwargs[':environment:']['receive']
        self.out['results'] = receive()


class Print(Filter):
    """
    Prints everything fed to it on stdout.
    """
    inputs = Types()

    def __init__(self, stream=None):
        """
        :param stream: stream to print to, defaults to sys.stdout
        :type stream: open :class:`file`
        """
        super(Print, self).__init__()

        self.stream = stream

    def _run(self, **kwargs):
        pprint(kwargs, stream=self.stream)


class Evaluation(Filter):
    """
    A Filter that allows to use an arbitrary function as a filter (i.e.
    makes a function act as a filter).

    .. warning::

        You should set ``inputs`` and ``outputs`` or no checking will take place.
        If ``inputs`` is set to ``None``, will run evaluator on ``input``.
    """

    def __init__(self, evaluator, inputs=None, outputs=None):
        """
        :param evaluator: function that evaluates
        :type evaluator: function
        :param inputs: input types
        :type inputs: :class:`~penchy.jobs.typecheck.Types`
        :param outputs: output types
        :type outputs: :class:`~penchy.jobs.typecheck.Types`
        """
        super(Evaluation, self).__init__()
        self.evaluator = evaluator
        self.inputs = util.default(inputs, Types())
        self.outputs = util.default(outputs, Types())

    def _run(self, **kwargs):
        if self.inputs == Types():
            if 'input' not in kwargs:
                raise ValueError('Evaluation inputs not set, expected input in arguments')
            else:
                args = {'input': kwargs['input']}
        else:
            try:
                args = dict([(name, kwargs[name]) for name in self.inputs.names])
            except KeyError:
                log.exception('Evaluator: expected arguments "{0}", got "{1}"'
                              .format(', '.join(sorted(self.inputs.names)),
                                      ', '.join(sorted(kwargs))))
                raise ValueError('Missing input')

        self.out = self.evaluator(**args)


class StatisticRuntimeEvaluation(Evaluation):
    """
    Filter to evaluate runtime statistically.

    Inputs:

    - ``times``: list of invocations of iterations of
                 the wallclocktime

    Outputs: see ``evaluate_runtimes``
    """
    inputs = Types(('times', list, list, int))
    outputs = Types(('averages', list, float),
                    ('maximals', list, int),
                    ('minimals', list, int),
                    ('positive_deviations', list, float),
                    ('negative_deviations', list, float))

    def __init__(self):
        super(StatisticRuntimeEvaluation, self).__init__(evaluate_runtimes,
                                                         self.inputs,
                                                         self.outputs)


def evaluate_runtimes(times):
    """
    Return the

    - averages: average times of iteration
    - maximals: the max times
    - positive_deviations: greatest positive deviation
    - minimals: the min times
    - negative_deviations: greatest negative deviations

    per iteration of all times.

    :param times: runtimes of all iterations of all iterations
    :type invocation: n*m 2D list
    :returns: the metrics described above in their order
    :rtype: dict
    """
    grouped_by_iteration = [[invocation[i] for invocation in times]
                            for i in range(len(times[0]))]

    maxs = [max(iteration) for iteration in grouped_by_iteration]
    mins = [min(iteration) for iteration in grouped_by_iteration]
    avgs = [stats.average(iteration) for iteration in grouped_by_iteration]
    pos_deviations = [abs(max_ - avg) / avg for max_, avg in zip(maxs, avgs)]
    neg_deviations = [abs(min_ - avg) / avg for min_, avg in zip(mins, avgs)]

    return {'averages': avgs,
            'maximals': maxs,
            'minimals': mins,
            'positive_deviations': pos_deviations,
            'negative_deviations': neg_deviations}


class Extract(Filter):
    """
    Extracts data out of the resultssets sent by the clients.

    This filter is useful if you want to pick just specific data from a specific
    :class:`~penchy.jobs.job.SystemComposition`. In the constructor you specify
    which data you want to extract by their name. If the name is not unique to
    all :class:`~penchy.jobs.job.SystemComposition` s you have to use a pair of
    the :class:`~penchy.jobs.job.SystemComposition` and the name, otherwise the
    Extract filter will use the first occurence in the ``results`` dictionary
    produced by :class:`~penchy.jobs.filters.Receive`. Both ways can be mixed.

    Example::

        composition1.flow = [ ... >> ['column1', 'column2'] >> send]
        composition2.flow = [ ... >> 'column1' >> send]

        extract = filters.Extract((composition2, 'column1'), 'column2')

        job = Job(compositions=...,
                  server_flow=[filters.Receive() >> extract >> ['column1', 'column2']]
                  )

    Inputs:
       - ``results``: Resultset as produced by the :class:`~penchy.jobs.filters.Receive` filter

    Outputs: The extracted data associated with the names specified in the constructor.
    """

    inputs = Types(('results', dict))

    def __init__(self, *args):
        """
        :param args: names of the data
        :type evaluator: list str or list (:class:`~penchy.jobs.job.SystemComposition`, str)
        """
        super(Extract, self).__init__()

        if not args:
            raise ValueError("Extract Filter needs at least one argument")

        # build the output types and check the given arguments
        names = []
        for col in args:
            if isinstance(try_unicode(col), unicode):
                names.append((col, object))
            else:
                try:
                    _, name = col
                except ValueError:
                    raise ValueError("Extract Filter takes only input names and pairs of system"
                                     "compositions and input names.")
                names.append((name, object))

        self.outputs = Types(*names)
        self.columns = args

    def _run(self, **kwargs):
        results = kwargs['results']
        for col in self.columns:

            # a system composition is not explicitly given
            if isinstance(try_unicode(col), unicode):

                # take the column from the first system composition and
                # warn if it appears in more than one
                found = False
                for res in results:
                    if col in results[res]:
                        if found:
                            log.warn("Column '{0}' is contained in more "
                                     "than one system composition".format(col))
                        else:
                            self.out[col] = results[res][col]
                            found = True
                if not found:
                    raise WrongInputError('Column is not contained in the resultset')
            # a system composition is given explicitly
            else:
                comp, column = col
                try:
                    self.out[column] = results[comp][column]
                except:
                    raise WrongInputError('Column is not contained in the resultset')


class Merge(Filter):
    """
    Merges the data with the given identifiers.

    This filter is useful if you want to combine data of the same kind
    from multiple :class:`~penchy.jobs.job.SystemComposition` s. If you think
    of the data as columns of a table, then the Merge filter basically puts
    these columns one below the other. To keep track of which columns came from
    where, you can put static values (identifiers) in an extra column.

    This is all configured in the constructor. The first argument defines the outputs
    of the filter by a tuple of names. In the table analogy it would be the header of the table. The
    second (and last) argument defines where the data comes from. It is a list of
    tuples. The tupels are the rows (possible multiple "rows", because the data form
    the system compositions might be multidimensional) of the table. In each tuple
    you have first the possiblity to define from which system composition the data
    is taken. If no system composition is given the first matching system composition
    will be used for the whole tuple. The rest of the tuple can consist either of data names or
    :class:`~penchy.jobs.filters.Value` objects. These Value objects are just a wrapper
    around an ordinary value to distinguish between data names and strings used as
    identifiers. Obviously the lenght of all tuples in the second argument have to be
    equal to the number of outputs specified in the first argument.

    Example::

        # Assume column1 of composition1 and composition2 are of the same kind
        # and column2 and column3 are of the same kind.
        composition1.flow = [ ... >> ['column1', 'column2'] >> send]
        composition2.flow = [ ... >> ['column1', 'column3'] >> send]

        merge = filters.Merge(('mergedcolumn1', 'mergedcolumn2'),
               [(composition1, 'column1'      , 'column2'      ),
                (composition2, 'column1'      , 'column3'      )])

        job = Job(compositions=...,
                  server_flow=[filters.Receive() >>
                               merge >> ['mergedcolumn1', 'mergedcolumn2'] >> ...
                  )

    Input:
       - ``results``: Resultset as produced by the :class:`~penchy.jobs.filters.Receive` filter

    Output: The columns specified in the constructor.
    """

    inputs = Types(('results', dict))

    def __init__(self, names, data):
        """
        :param names: names of outputs
        :type names: tuple string
        :param data: the columns that should be merged and the identifiers
        :type data: tuple (:class:`~penchy.jobs.job.SystemComposition`, string,
                           :class:`~penchy.jobs.filters.Value`)
        """
        super(Merge, self).__init__()
        self.data = data
        self.names = names
        self.outputs = Types(*[(n, object) for n in names])

        for row in data:
            if (isinstance(try_unicode(row[0]), unicode) or
                isinstance(row[0], Value)):
                n = len(row)
            else:
                n = len(row[1:])

            if n > len(names):
                raise ValueError("More outputs are used then are defined.")
            if n < len(names):
                raise ValueError("Not all defined outputs are used.")

            # We can not cover row[0] because importing SystemComposition
            # would lead to cyclic imports
            for field in row[1:]:
                if not (isinstance(try_unicode(field), unicode) or
                        isinstance(field, Value)):
                    raise ValueError("Given value is neither a string nor"
                                     "wrapped by Value.")

    def _run(self, **kwargs):
        results = kwargs['results']
        for row in self.data:
            # check if a system composition is explicitly given for that row
            if not isinstance(try_unicode(row[0]), unicode):
                comp = row[0]
                row = row[1:]
            else:
                comp = None

            # Everything in this row is taken from the same system composition
            for name, field in zip(self.names, row):

                # if it is a column, extract it from the right composition
                if isinstance(try_unicode(field), unicode):
                    if comp is None:
                        for c in results:
                            if field in results[c]:
                                comp = c
                                break
                    try:
                        self.out[name].append(results[comp][field])
                    except KeyError:
                        raise WrongInputError('Column "{0}" is not contained in the resultset'.format(field))

                # if it is a ``Value``, just append it
                elif isinstance(field, Value):
                    self.out[name].append(field.value)


class ExtractingReceive(Receive, Extract):
    """
    A composition of the :class:`~penchy.jobs.filters.Receive` and
    :class:`~penchy.jobs.filters.Extract` filter.
    """
    inputs = Types((':environment:', dict))

    def __init__(self, *args):
        Extract.__init__(self, *args)
        Receive.__init__(self)

    def _run(self, **kwargs):
        Receive._run(self, **kwargs)
        results = self.out['results']
        self.reset()
        Extract._run(self, results=results)


class MergingReceive(Receive, Merge):
    """
    A composition of the :class:`~penchy.jobs.filters.Receive` and
    :class:`~penchy.jobs.filters.Merge` filter.
    """
    inputs = Types((':environment:', dict))

    def __init__(self, names, data):
        Merge.__init__(self, names, data)
        Receive.__init__(self)

    def _run(self, **kwargs):
        Receive._run(self, **kwargs)
        results = self.out['results']
        self.reset()
        Merge._run(self, results=results)


class Map(Filter):
    """
    Returns a list constructed by applying a filter to all
    elements in the given list.

    The applied filter needs exactly one in- and output. If
    the filter has more than one in- and output, it is possible
    to pick one with ``finput`` and ``foutput``.
    """

    def __init__(self, filter_, input='values', output='values', finput=None,
                 foutput=None):
        """
        :param filter_: the filter to be applied
        :type filter_: :class:`~penchy.jobs.elements.Filter`
        :param input: the name of the input of :class:`~penchy.jobs.filters.Map`
        :type input: string
        :param output: the name of the output of :class:`~penchy.jobs.filters.Map`
        :type output: string
        :param finput: the name of an input of the applied filter
        :type finput: string
        :param foutput: the name of an output of the applied filter
        :type foutput: string
        """
        super(Map, self).__init__()
        self.input = input
        self.output = output
        input_desc = filter_.inputs.descriptions
        output_desc = filter_.outputs.descriptions

        if finput is None and (input_desc is None or len(input_desc) != 1):
            raise TypeCheckError('Map takes only filters with exactly one input '
                                 'or you have to specify which input shall be used.')
        if foutput is None and (output_desc is None or len(output_desc) != 1):
            raise TypeCheckError('Map takes only filters with exactly one output'
                                 'or you have to specify which output shall be used.')

        self.finput = filter_.inputs.names.pop() if finput is None else finput
        self.foutput = filter_.outputs.names.pop() if foutput is None else foutput

        input_types = input_desc[self.finput]
        self.inputs = Types((self.input, list) + input_types)

        output_types = output_desc[self.foutput]
        self.outputs = Types((self.output, list) + output_types)

        self.filter = filter_

    def _run(self, **kwargs):
        for v in kwargs[self.input]:
            param = {self.finput: v}
            self.filter._run(**param)
            self.out[self.output].append(self.filter.out[self.foutput])
            self.filter.reset()


class Upload(Filter):  # pragma: no cover
    """
    Uploads a plot to a remote machine.

    Inputs:

    - ``filename``: The filename of the plot file to upload
    """
    inputs = Types(('filename', path))

    def __init__(self, method, remote_path, *args, **kwargs):
        """
        :param method: method to use
        :type method: descendant of :class:`~penchy.deploy.Deploy`
        :param remote_path: path to upload to
        :type path: str

        Additionally, you can pass any arguments you'd normally
        pass to your implementation of :class:`~penchy.deploy.Deploy`

        A simple way to use this might be::

            upload = filters.Upload(SFTPDeploy, '/tmp/foo.svg', '0x0b.de', 'me', 'pass')

            job = Job(composition=comp1)
                server_flow=[
                    ... >> plot >> upload

        The credentials can also be extracted from maven's :file:`settings.xml`
        like so::

            upload = filters.Upload(SFTPDeploy, '/tmp/foo.svg', '0x0b.de',
                                    *extract_maven_credentials('0x0b'))

        where ``0x0b`` is the id of this server as defined in :file:`settings.xml`.
        """
        super(Upload, self).__init__()
        if not issubclass(method, Deploy):
            raise ValueError('deploy must be a descendant of ``Deploy``')

        self.method = method
        self.remote_path = remote_path
        self.args = args
        self.kwargs = kwargs

    def _run(self, **kwargs):
        method = self.method(*self.args, **self.kwargs)
        with method.connection_required():
            method.put(kwargs['filename'], self.remote_path)


class Dump(SystemFilter):
    """
    Dumps everything sent to it as JSON encoded string.

    No typechecking on inputs takes place. Every input must be JSON encodable
    and will be included in the dump.

    JSON format consists of one dictionary that includes

    - the dictionary ``system`` which describes the system (JVM, Workload, Tool,
      SystemComposition, PenchY descriptions and versions, parts will miss if
      executed as part of the server pipeline)

    - the dictionary ``data`` which contains all data sent to :class:`Dump`
      (with the name of the input as key)

    Outputs:

    - ``dump``: JSON encoded data along job and system information.
    """
    inputs = Types()
    outputs = Types(('dump', str))

    def __init__(self, include_complete_job=False, indent=None):
        super(Dump, self).__init__()
        self.include = include_complete_job
        self.indent = indent

    def _run(self, **kwargs):
        # collect and include system information
        env = kwargs.pop(':environment:')
        if self.include:
            with open(env['job']) as f:
                job = f.read()
        else:
            job = os.path.basename(env['job'])
        system = {
            'job': job,
            'penchy': __version__
        }
        if env['current_composition'] is not None:
            comp = env['current_composition']
            system['composition'] = comp.__str__(),
            system['jvm'] = comp.jvm.information()
            classes = set(e.__class__ for e in comp.elements)
            system['dependencies'] = dict((c.__name__, [dep.__str__() for dep
                                                        in c.DEPENDENCIES])
                                           for c in classes
                                          if c.DEPENDENCIES)
        dump = {
            'system': system,
            'data': kwargs
        }
        s = json.dumps(dump, indent=self.indent)
        self.out['dump'] = s


class Save(SystemFilter):
    """
    Copies content of path to specified location.

    Inputs:

    - ``data``: data to save (encoded)  # TODO: cofi
    """
    inputs = Types(('data', (str, unicode)))

    def __init__(self, target_path):
        """
        :param target_path: path to destination relative to
                            :class:`~penchy.jobs.job.NodeSetting`.path (on
                            client), to working directory (on server) or
                            absolute
        :type target_path: str
        """
        super(Save, self).__init__()
        self.target_path = target_path

    def _run(self, **kwargs):
        if not os.path.isabs(self.target_path) \
           and kwargs[':environment:']['current_composition'] is not None:
            node_setting = kwargs[':environment:']['current_composition'].node_setting
            self.target_path = os.path.join(node_setting.path, self.target_path)
        log.debug('Save to "{0}"'.format(os.path.abspath(self.target_path)))
        with open(self.target_path, 'w') as f:
            write(f, kwargs['data'])


class BackupFile(SystemFilter):
    """
    Copies content of path to specified location.

    Inputs:

    - ``filename``: path of file to backup
    """
    inputs = Types(('filename', path))

    def __init__(self, target_path):
        """
        :param target_path: path to destination relative to
                            :class:`~penchy.jobs.job.NodeSetting`.path (on
                            client), to working directory (on server) or
                            absolute
        :type target_path: str
        """
        super(BackupFile, self).__init__()
        self.target_path = target_path

    def _run(self, **kwargs):
        if not os.path.isabs(self.target_path) \
           and kwargs[':environment:']['current_composition'] is not None:
            node_setting = kwargs[':environment:']['current_composition'].node_setting
            self.target_path = os.path.join(node_setting.path, self.target_path)
        path = kwargs['filename']
        if not os.path.exists(path):
            raise WrongInputError('file {0} does not exist'.format(path))
        log.debug('Backup "{0}" to "{1}"'.format(os.path.abspath(path),
                                                 os.path.abspath(self.target_path)))
        shutil.copyfile(path, self.target_path)


class Read(Filter):
    """
    Reads and returns the content of filepaths.

    Inputs:

    - ``paths``: the filepaths to read

    Outputs:

    - ``data``: the content of the filepaths
    """
    inputs = Types(('paths', list, path))
    outputs = Types(('data', list, str))

    def _run(self, **kwargs):
        paths = kwargs['paths']
        data = []
        for p in paths:
            log.debug('Reading "{0}"'.format(os.path.abspath(p)))
            with open(p, 'rb') as f:
                data.append(f.read())
        self.out['data'] = data


class Unpack(Filter):
    """
    Reduces a singleton list to its only element.

    Input (default names):

    - ``singleton``: the singleton list

    Outputs (default names):

    - ``result``: the extracted element

    .. warning::

        Raises :class:`~penchy.jobs.filters.WrongInputError` if the list
        has not exactly one element.
    """

    def __init__(self, input='singleton', output='result'):
        """
        :param input: the name of the input
        :type input: string
        :param output: the name of the output
        :type output: string
        """
        super(Unpack, self).__init__()
        self.input = input
        self.output = output
        self.inputs = Types((input, list))
        self.outputs = Types((output, object))

    def _run(self, **kwargs):
        singleton = kwargs[self.input]
        if len(singleton) > 1:
            raise WrongInputError('The list has more than one element.')
        if len(singleton) < 1:
            raise WrongInputError('The list is empty.')
        value = singleton.pop()
        self.out[self.output] = value


class Mean(Filter):
    """
    Computes the mean of given values.

    Inputs:

    - ``values``: numeric values

    Outputs:

    - ``mean``: mean of the numeric values
    """
    inputs = Types(('values', list, (int, float)))
    outputs = Types(('mean', float))

    def _run(self, **kwargs):
        self.out['mean'] = stats.average(kwargs['values'])


class StandardDeviation(Filter):
    """
    Computes the standard deviation of given values.

    Inputs:

    - ``values``: numeric values

    Outputs:

    - ``standard_deviation``: mean of the numeric values
    """
    inputs = Types(('values', list, (int, float)))
    outputs = Types(('standard_deviation', float))

    def __init__(self, ddof=1):
        """
        :param ddof: Delta Degrees of Freedom (ddof): ``ddof``
                     is substracted from the divisor.
        :type ddof: integer
        """
        super(StandardDeviation, self).__init__()
        self.ddof = ddof

    def _run(self, **kwargs):
        vs = kwargs['values']
        std = stats.standard_deviation(vs, self.ddof)
        self.out['standard_deviation'] = std


class Sum(Filter):
    """
    Computes the sum of a list of numbers.

    Inputs (default names):

    - ``values``: list of numbers

    Outputs (default names):

    - ``sum``: sum of the list of numbers
    """

    inputs = Types(('values', list, (int, float)))
    outputs = Types(('sum', (int, float)))

    def __init__(self, input='values', output='sum'):
        super(Sum, self).__init__()
        self.input = input
        self.output = output

    def _run(self, **kwargs):
        self.out[self.output] = sum(kwargs[self.input])


class Enumerate(Filter):
    """
    Enumerates the given values.

    Inputs:

    - ``values``: a list of arbitrary objects

    Outputs:

    - ``values``: the same list of arbitrary objects
    - ``numbers``: a list of numbers
    """

    inputs = Types(('values', list))
    outputs = Types(('values', list),
                    ('numbers', list, int))

    def __init__(self, start=0, step=1):
        """
        :param start: start value of the enumeration
        :type start: int
        :param step: step size of the enumeration
        :type step: int
        """
        super(Enumerate, self).__init__()
        self.start = start
        self.step = step

    def _run(self, **kwargs):
        self.out['values'] = kwargs['values']
        self.out['numbers'] = list(range(self.start,
                                         self.start + len(kwargs['values'] * self.step),
                                         self.step))


class Decorate(Filter):
    """
    Decorates the inputs with the a given string. By default the filter
    has only the input ``values``, but it is possible to specify the inputs
    with the argument ``inputs``. The interpolation syntax '{i}' where ``i``
    is the position of the input value.

    Inputs (default names):

    - ``values``: a list of int or float values that shall be decorated

    Outputs:

    - ``values``: the decorated list
    """
    outputs = Types(('values', list, str))

    def __init__(self, string, inputs=['values']):
        """
        :param string: the decorate/interpolation string
        :type string: string
        :param inputs: list of input names
        :type inputs: list string
        """
        super(Decorate, self).__init__()

        self.inputs = Types(*[(i, list, (int, float)) for i in inputs])
        self.string = string

    def _run(self, **kwargs):
        values = zip(*[kwargs[name] for name in self.inputs.names])
        self.out['values'] = [self.string.format(*v) for v in values]


class ConfidenceIntervalMean(Filter):
    """
    A filter that computes the confidence intervall for the mean.
    The implementation is based on the paper 'Statisically Rigorous
    Java Performance Evaluation' by Andy Georges et.al.

    .. note::

        It is assumed that the samples are statistically independend.
    """
    inputs = Types(('values', list, (int, float)))
    outputs = Types(('interval', tuple, float))

    def __init__(self, significance_level):
        """
        :param significance_level: the significance level for the confidence interval
        :type significance_level: float
        """
        super(ConfidenceIntervalMean, self).__init__()
        self.sig_level = significance_level

    def _run(self, **kwargs):
        # Gaussian distribution
        from scipy.stats import norm
        # Students t-distribution
        from scipy.stats import t

        xs = kwargs['values']

        # These computations are common to both of the following two cases
        n = len(xs)
        avg = stats.average(xs)
        s = stats.standard_deviation(xs, ddof=1)

        # If the number of samples is large
        if n > 29:
            d = norm.ppf(1 - self.sig_level / 2)

        # If the number of samples is small
        else:
            d = t.ppf(1 - self.sig_level / 2, n - 1)

        c1 = avg - d * s / math.sqrt(n)
        c2 = avg + d * s / math.sqrt(n)
        self.out['interval'] = (c1, c2)


class CI2Alternatives(Filter):
    """
    A filter that computes the confidence interval for the mean of
    two alternatives.
    The implementation is based on the paper 'Statisically Rigorous
    Java Performance Evaluation' by Andy Georges et.al.

    .. note::

        If the resulting confidence interval includes zero, we can
        conclude, at the confidence level choosen, that there is no
        statistically significant diffeence between the two alternatives.

    .. note::

        It is assumed that the samples are statistically independend.
    """
    inputs = Types(('xs', list, (int, float)),
                   ('ys', list, (int, float)))
    outputs = Types(('interval', tuple, float))

    def __init__(self, significance_level):
        """
        :param significance_level: the significance level for the confidence interval
        :type significance_level: float
        """
        super(CI2Alternatives, self).__init__()
        self.sig_level = significance_level

    def _run(self, **kwargs):
        # Gaussian distribution
        from scipy.stats import norm
        # Students t-distribution
        from scipy.stats import t

        xs = kwargs['xs']
        ys = kwargs['ys']

        # These computations are common to both of the following two cases
        n1, n2 = len(xs), len(ys)
        s1 = stats.standard_deviation(xs, ddof=1)
        s2 = stats.standard_deviation(ys, ddof=1)
        sx = math.sqrt((s1 ** 2) / n1 + (s2 ** 2) / n2)
        avgx = stats.average(xs)
        avgy = stats.average(ys)
        avg = avgx - avgy

        # If the number of samples is large in both samples
        if n1 > 29 and n2 > 29:
            d = norm.ppf(1 - self.sig_level / 2)

        # If the number of samples is small in at least one sample
        else:
            numerator = (s1 ** 2 / n1 + s2 ** 2 / n2) ** 2
            denumerator = (s1 ** 2 / n1) ** 2 / (n1 - 1) + (s2 ** 2 / n2) ** 2 / (n2 - 1)
            ndf = numerator / denumerator
            d = t.ppf(1 - self.sig_level / 2, round(ndf, 0))

        c1 = avg - d * sx
        c2 = avg + d * sx
        self.out['interval'] = (c1, c2)


class DropFirst(Filter):
    """
    This filter drops the first element of a list.

    For example it can be used to discard the first iteration of a measurement
    to reach indepedency of the measurements.

    Inputs:

    - ``values``: a list of values

    Outputs:

    - ``values``: a list of values without the first element
    """
    inputs = Types(('values', list, object))
    outputs = Types(('values', list, object))

    def _run(self, **kwargs):
        self.out['values'] = kwargs['values'][1:]


class SteadyState(Filter):
    """
    Determines for each invocation the iteration where steady-state performance is
    reached and suppose that we want to retain ``k`` measurements per invocation.
    I.e. once the coefficient of variation of the ``k`` iterations falls below
    ``threshold`` (typically 0.01 or 0.02).

    Inputs:

    - ``values``: 2d list of measurements

    Outputs:

    - ``values``: 2d list of steady-state iterations
    """
    inputs = Types(('values', list, list, (int, float)))
    outputs = Types(('values', list, list, (int, float)))

    def __init__(self, k, threshold):
        super(SteadyState, self).__init__()
        self.threshold = threshold
        self.k = k

    def _run(self, **kwargs):
        xss = kwargs['values']

        for xs in xss:
            for i in range(0, len(xs) - self.k):
                if stats.coefficient_of_variation(xs[i:self.k + i]) < self.threshold:
                    self.out['values'].append(xs[i:self.k + i])
                    break


class Sort(Filter):
    """
    Sorts the table (i.e. the inputs) by the columns specified
    in ``sort_by``.

    Inputs: the (unsorted) table
    Outputs: the sorted table

    .. warning::

        Since this filter is very generic no typechecking will
        take place.
    """
    inputs = Types()
    outputs = Types()

    def __init__(self, sort_by, reverse=False):
        """
        :param sort_by: the table is sorted by these columns
        :type sort_by: string or list string
        :param reverse: order the table in reverse
        :type reverse: bool
        """
        super(Sort, self).__init__()
        if isinstance(sort_by, list):
            self.sort_by = sort_by
        else:
            self.sort_by = [sort_by]
        self.reverse = reverse

    def _run(self, **kwargs):
        # Split the dict in its keys and values
        names = list(kwargs)
        values = zip(*kwargs.values())

        # Get the posisitions of the columns in ``sort_by``
        columns = [i for i, x in enumerate(names) if x in self.sort_by]

        # Sort the table
        for column in reversed(columns):
            values = sorted(values, key=operator.itemgetter(column),
                            reverse=self.reverse)

        for name, value in zip(names, zip(*values)):
            self.out[name] = list(value)


class Accumulate(Filter):
    """
    Accumulates the numbers in the given column and writes every partial
    sum into a column accum.

    Inputs: One input ``name`` (where ``name`` is configurable via
            the constructor) that is a list of numbers.

    Outputs:

    - ``accum``: The accumulated values.
    """
    outputs = Types(('accum', list, float))

    def __init__(self, name):
        """
        :param name: name of the input
        :type name: string
        """
        super(Accumulate, self).__init__()
        self.name = name
        self.inputs = Types((name, list, (int, float)))

    def _run(self, **kwargs):
        numbers = kwargs[self.name]

        accum = 0
        for n in numbers:
            accum += n
            self.out['accum'].append(accum)


class Normalize(Filter):
    """
    Normalizes ``numbers`` according to a given number ``n``.

    FIXME: Better names for inputs
    Inputs:

    - ``values``: a list of numbers
    - ``norm``: the number normalized by

    Outputs:

    - ``values``: a list of normalized numbers
    """
    inputs = Types(('values', list, (int, float)),
                   ('norm', (int, float)))
    outputs = Types(('values', list, float))

    def __init__(self, epsilon=0.0001):
        """
        :param epsilon: if the normalized sum differes more than ``epsilon``
                        from 1.0 a warning is given.
        :type espilon: float
        """
        super(Normalize, self).__init__()
        self.epsilon = epsilon

    def _run(self, **kwargs):
        numbers = kwargs['values']
        n = kwargs['norm']

        for number in numbers:
            self.out['values'].append(number / n)

        if abs(1.0 - sum(self.out['values'])) < self.epsilon:
            log.warn("The normalized sum differes more than {0} from 1.0".format(self.epsilon))


class Zip(Filter):
    """
    This filter Zips a list of lists

    Inputs:

    - ``values``: a list of values

    Outputs:

    - ``values``: a list of values (zipped)
    """
    inputs = Types(('values', list, list, object))
    outputs = Types(('values', list, list, object))

    def _run(self, **kwargs):
        self.out['values'] = [list(l) for l in zip(*kwargs['values'])]

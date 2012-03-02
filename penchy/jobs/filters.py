"""
This module provides filters.

Inputs are fed to filters via keywords in the ``run`` method.
Outputs are available via the ``out`` attribute.

 .. moduleauthor:: Michael Markert <markert.michael@googlemail.com>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import itertools
import json
import logging
import os
import re
import shutil
import math
from pprint import pprint

from penchy import __version__
from penchy.compat import str, path, unicode, to_unicode
from penchy.jobs.elements import Filter, SystemFilter
from penchy.jobs.typecheck import Types, TypeCheckError
from penchy.util import default, average, Value


log = logging.getLogger(__name__)


class WrongInputError(Exception):
    """
    Filter received input it was not expecting and cannot process.
    """
    pass


class Tamiflex(Filter):
    pass


class HProfCpuTimes(Filter):
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
    inputs = Types(('hprof', list, path))

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
        \s+(?P<method>(\w|\.|\$)+)
        """, re.VERBOSE)

    def _run(self, **kwargs):
        files = kwargs['hprof']

        for f in files:
            data = {'rank': [],
                    'selftime': [],
                    'accum': [],
                    'count': [],
                    'trace': [],
                    'method': []}

            with open(f) as fobj:
                for line in fobj:
                    if line.startswith('CPU TIME (ms) BEGIN'):
                        break
                # we did not break, i.e. no begin marker was found
                else:
                    raise WrongInputError("Marker 'CPU TIME (ms) BEGIN' not found.")

                s = self._TOTAL_RE.search(line)
                if s is None:
                    log.error('Received invalid input:\n{0}'.format(line))
                    raise WrongInputError('Received invalid input.')
                total = s.groups()[0]
                self.out['total'].append(int(total))

                # Jump over the heading
                next(fobj)

                for line in fobj:
                    if line.startswith('CPU TIME (ms) END'):
                        break
                    m = self._DATA_RE.match(line)
                    if m is None:
                        log.error('Received invalid input:\n{0}'.format(line))
                        raise WrongInputError('Received invalid input.')
                    result = self._DATA_RE.match(line).groupdict()

                    data['rank'].append(int(result['rank']))
                    data['selftime'].append(float(result['selftime']))
                    data['accum'].append(float(result['accum']))
                    data['count'].append(int(result['count']))
                    data['trace'].append(int(result['trace']))
                    data['method'].append(result['method'])

                # we did not break, i.e. no end marker was found
                else:
                    raise WrongInputError("Marker 'CPU TIME (ms) END' not found.")

                for key, val in data.items():
                    self.out[key].append(val)


class DacapoHarness(Filter):
    """
    Filters output of a DaCapo Harness.

    Inputs:

    - ``stderr``:  List of Paths to stderror output files
    - ``exit_code``: List of program exit codes

    Outputs:

    - ``failures``: failure count per invocation
    - ``times``: execution time per itertion per invocation
    - ``valid``: flag that indicates if execution was valid
    """
    inputs = Types(('stderr', list, path),
                   ('exit_code', list, int))

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
        exit_codes = kwargs['exit_code']
        stderror = kwargs['stderr']

        for f, exit_code in zip(stderror, exit_codes):
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
            self.out['valid'].append(exit_code == 0 and failures == 0)


class Send(SystemFilter):
    """
    Send data to the server.

    Inputs:

    - ``:environment:``: see :meth:`Job._build_environment`
    - ``payload``: data to send
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
        self.inputs = default(inputs, Types())
        self.outputs = default(outputs, Types())

    def _run(self, **kwargs):
        if self.inputs == Types():
            if 'input' not in kwargs:
                raise ValueError('Evaluation inputs not set, expected input in arguments')
            else:
                args = {'input' : kwargs['input']}
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
    outputs = Types(('averages', list, int),
                    ('maximals', list, int),
                    ('minimals', list, int),
                    ('positive_deviations', list, int),
                    ('negative_deviations', list, int))

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
    avgs = [average(iteration) for iteration in grouped_by_iteration]
    pos_deviations = [abs(max_ - avg) / avg for max_, avg in zip(maxs, avgs)]
    neg_deviations = [abs(min_ - avg) / avg for min_, avg in zip(mins, avgs)]

    return {'averages' : avgs,
            'maximals' : maxs,
            'minimals' : mins,
            'positive_deviations' : pos_deviations,
            'negative_deviations' : neg_deviations}


class Aggregate(Filter):
    """
    Extracts data out of the resultssets sent by the clients.

    Input:
       - ``results``: Resultset as produced by the :class:`~penchy.jobs.filters.Receive` filter

    Output: The extracted data associated with the names specified in the constructor.
    """

    inputs = Types(('results', dict))

    def __init__(self, *args):
        """
        :param args: names of the data
        :type evaluator: list str or list (:class:`~penchy.jobs.job.SystemComposition`, str)
        """
        super(Aggregate, self).__init__()

        if not args:
            raise ValueError("Aggregate Filter needs at least one argument")

        names = []
        for col in args:
            if isinstance(to_unicode(col), unicode):
                names.append((col, object))
            else:
                try:
                    _, name = col
                except ValueError:
                    raise ValueError("Aggregate Filter takes only input names and pairs of system"
                                     "compositions and input names.")
                names.append((name, object))

        self.outputs = Types(*names)
        self.columns = args

    def _run(self, **kwargs):
        results = kwargs['results']
        for col in self.columns:
            if isinstance(to_unicode(col), unicode):
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
            else:
                comp, column = col
                try:
                    self.out[column] = results[comp][column]
                except:
                    raise WrongInputError('Column is not contained in the resultset')


class Condense(Filter):
    # FIXME: Condense has no class attribute ``names`` as indicated here
    """
    Merges the data with the given identifiers

    Input:
       - ``results``: Resultset as produced by the ``Receive`` filter

    Output: The columns specified in `Condense.names`
    """

    inputs = Types(('results', dict))

    def __init__(self, names, data):
        super(Condense, self).__init__()
        self.data = data
        self.names = names
        self.outputs = Types(*[(n, object) for n in names])

    def _run(self, **kwargs):
        results = kwargs['results']
        for row in self.data:
            #FIXME: Check for isinstance(first, SystemComposition)
            if not isinstance(to_unicode(row[0]), unicode):
                comp = row[0]
                row = row[1:]
            else:
                comp = None

            # Everything is taken from the same system composition
            for name, field in zip(self.names, row):
                if isinstance(to_unicode(field), unicode):
                    if comp is None:
                        for c in results:
                            if field in results[c]:
                                comp = c
                                break
                    try:
                        self.out[name].append(results[comp][field])
                    except KeyError:
                        raise WrongInputError('Column "{0}" is not contained in the resultset'.format(field))
                elif isinstance(field, Value):
                    self.out[name].append(field.value)
                else:
                    #FIXME: Catch this error before running the job
                    raise ValueError("Condense filter is malformed.")


class AggregatingReceive(Receive, Aggregate):
    """
    A composition of the ``Receive`` and ``Aggregate`` filter.
    """
    inputs = Types((':environment:', dict))

    def __init__(self, *args):
        Aggregate.__init__(self, *args)
        Receive.__init__(self)

    def _run(self, **kwargs):
        Receive._run(self, **kwargs)
        results = self.out['results']
        self.reset()
        Aggregate._run(self, results=results)


class CondensingReceive(Receive, Condense):
    """
    A composition of the ``Receive`` and ``Condense`` filter.
    """
    inputs = Types((':environment:', dict))

    def __init__(self, names, data):
        Condense.__init__(self, names, data)
        Receive.__init__(self)

    def _run(self, **kwargs):
        Receive._run(self, **kwargs)
        results = self.out['results']
        self.reset()
        Condense._run(self, results=results)


class Map(Filter):
    """
    Returns a list constructed by applying a filter to all
    elements in the given list.
    """

    def __init__(self, filter_, input='values', output='result', finput=None, foutput=None):
        super(Map, self).__init__()
        self.input = input
        self.output = output
        input_desc = filter_.inputs.descriptions
        output_desc = filter_.outputs.descriptions

        if finput is None and (input_desc is None or len(input_desc) != 1):
            raise TypeCheckError("Map takes only filters with exactly one input")
        if foutput is None and (output_desc is None or len(output_desc) != 1):
            raise TypeCheckError("Map takes only filters with exactly one output")

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


class Upload(Filter):
    pass


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
            'job' : job,
            'penchy' : __version__
        }
        if env['current_composition'] is not None:
            comp = env['current_composition']
            system['composition'] = str(comp),
            system['jvm'] = comp.jvm.information()
            classes = set(e.__class__ for e in comp.elements)
            system['dependencies'] = dict((c.__name__, [str(dep) for dep
                                                        in c.DEPENDENCIES])
                                           for c in classes
                                          if c.DEPENDENCIES)
        dump = {
            'system' : system,
            'data' : kwargs
        }
        s = json.dumps(dump, indent=self.indent)
        self.out['dump'] = s


class Save(SystemFilter):
    """
    Copies content of path to specified location.

    Inputs:

    - ``data``: data to save (encoded)
    """
    inputs = Types(('data', path))

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
            f.write(kwargs['data'])


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
    outputs = Types(('data', list, path))

    def _run(self, **kwargs):
        paths = kwargs['paths']
        data = []
        for p in paths:
            log.debug('Reading "{0}"'.format(os.path.abspath(p)))
            with open(p) as f:
                data.append(f.read())
        self.out['data'] = data


class Unpack(Filter):
    """
    Reduces a singleton list to its only element.
    """

    def __init__(self, input='singleton', output='result'):
        super(Unpack, self).__init__()
        self.input = input
        self.output = output
        self.inputs = Types((input, list))
        self.outputs = Types((output, object))

    def _run(self, **kwargs):
        singleton = kwargs[self.input]
        if len(singleton) != 1:
            raise WrongInputError('The list has more than one element.')
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
        self.out['mean'] = average(kwargs['values'])


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
        super(StandardDeviation, self).__init__()
        self.ddof = ddof

    def _run(self, **kwargs):
        vs = kwargs['values']
        avg = average(vs)
        std = math.sqrt(sum((v - avg) ** 2 for v in vs) / (len(vs) - self.ddof))
        self.out['standard_deviation'] = std


class Sum(Filter):
    """
    Computes the sum of a list of integers or floats

    Inputs:
    - ``values``: numeric values

    Outputs:
    - ``sum``: sum of the numeric values
    """

    inputs = Types(('values', list, (int, float)))
    outputs = Types(('sum', (int, float)))

    def _run(self, **kwargs):
        self.out['sum'] = sum(kwargs['values'])


class Enumerate(Filter):
    # FIXME: Document my inputs & outputs
    """
    Enumerates the given values.

    Inputs:
    - ``values``

    Outputs:
    - ``values``
    - ``numbers``
    """

    inputs = Types(('values', list))
    outputs = Types(('values', list),
                    ('numbers', list, int))

    def __init__(self, start=0, step=1):
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
    Decorates the inputs with the a given string.

    Inputs:
    - ``values``

    Outputs:
    - ``values``
    """

    inputs = Types(('values', list, (int, float)))
    outputs = Types(('values', list, str))

    def __init__(self, string):
        super(Decorate, self).__init__()
        self.string = string

    #TODO: Multiple Inputs?
    def _run(self, **kwargs):
        self.out['values'] = [self.string.format(v) for v in kwargs['values']]

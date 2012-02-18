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
import numpy
from pprint import pprint

from penchy import __version__
from penchy.jobs.elements import Filter, SystemFilter
from penchy.jobs.typecheck import Types
from penchy.util import default, average


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
    inputs = Types(('hprof', list, str))

    outputs = Types(('total', list, int),
                    ('rank', list, list, int),
                    ('self', list, list, float),
                    ('accum', list, list, float),
                    ('count', list, list, int),
                    ('trace', list, list, int),
                    ('method', list, list, str))

    _TOTAL_RE = re.compile('total = (\d+)')
    _DATA_RE = re.compile("""
        \s+(?P<rank>\d+)
        \s+(?P<self>\d+\.\d{2})%
        \s+(?P<accum>\d+\.\d{2})%
        \s+(?P<count>\d+)
        \s+(?P<trace>\d+)
        \s+(?P<method>(\w|\.|\$)+)
        """, re.VERBOSE)

    def _run(self, **kwargs):
        files = kwargs['hprof']

        for f in files:
            data = {'rank': [],
                    'self': [],
                    'accum': [],
                    'count': [],
                    'trace': [],
                    'method': []}

            with open(f) as fobj:
                line = fobj.readline()
                while not line.startswith("CPU TIME (ms) BEGIN"):
                    line = fobj.readline()
                    if not line:
                        raise WrongInputError("Marker 'CPU TIME (ms) BEGIN' not found.")
                s = self._TOTAL_RE.search(line)
                if s is None:
                    log.error('Received invalid input:\n{0}'.format(line))
                    raise WrongInputError('Received invalid input.')
                total = s.groups()[0]
                self.out['total'].append(int(total))

                # Jump over the heading
                fobj.readline()

                line = fobj.readline()
                while not line.startswith("CPU TIME (ms) END"):
                    m = self._DATA_RE.match(line)
                    if m is None:
                        log.error('Received invalid input:\n{0}'.format(line))
                        raise WrongInputError('Received invalid input.')
                    result = self._DATA_RE.match(line).groupdict()
                    dict((k, data.get(k).append(result.get(k)))
                           for k in data.keys())
                    line = fobj.readline()
                    if not line:
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
    inputs = Types(('stderr', list, str),
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

    - ``environment``: see :meth:`Job._build_environment`
    - ``payload``: data to send
    """
    # FIXME: Make environment a special name for SystemFilter
    # to avoid name clashes
    inputs = Types()

    def _run(self, **kwargs):
        send = kwargs.pop('environment')['send']
        send(kwargs)


class Receive(SystemFilter):
    """
    Makes received data available for the serverside pipeline.

    Inputs:

    - ``environment``: see :meth:`Job._build_environment`

    Outputs:

    - ``results``: dict that maps :class:`SystemComposition` to their results.
    """
    inputs = Types(('environment', dict))
    outputs = Types(('results', dict))

    def _run(self, **kwargs):
        receive = kwargs['environment']['receive']
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
                              .format(', '.join(i[0] for i in self.inputs.descriptions),
                                      ', '.join(k for k in kwargs)))
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
    Extracts data out of the resultssets send by the clients.

    Input:
       - ``results``: Resultset as produced by the ``Receive`` filter

    Output: The columns specified in `Aggregate.columns`
    """

    inputs = Types(('results', dict))

    def __init__(self, *args):
        super(Aggregate, self).__init__()
        self.columns = args

    def _run(self, **kwargs):
        results = kwargs['results']
        names = []
        for col in self.columns:
            if isinstance(col, str):
                found = False
                for res in results:
                    if col in results[res].keys():
                        if found:
                            log.warn("Column '{0}' is contained in more " +
                                     "than one system composition".format(col))
                        else:
                            self.out[col] = results[res][col]
                            names.append((col, object))
                            found = True
                if not found:
                    raise WrongInputError("Column is not contained " +
                                          "in the resultset")
            else:
                comp, column = col
                try:
                    self.out[column] = results[comp][column]
                except:
                    raise WrongInputError("Column is not contained " +
                                          "in the resultset")
                names.append((column, object))
        self.outputs = apply(Types, names)


class Condense(Filter):
    """
    Merges the data with the given identifiers

    Input:
       - ``results``: Resultset as produced by the ``Receive`` filter

    Output: The columns specified in `Condense.names`
    """

    inputs = Types(('results', dict))

    def __init__(self, data, names):
        super(Condense, self).__init__()
        self.data = data
        self.names = names
        self.outputs = apply(Types, [(n, object) for n in names])

    def _run(self, **kwargs):
        results = kwargs['results']
        for cols in self.data:
            col = ""
            ids = []
            if isinstance(cols[0], str):
                found = False
                for res in results:
                    if cols[0] in results[res].keys():
                        if found:
                            log.warn("Column '{0}' is contained in more " +
                                     "than one system composition".format(cols[0]))
                        else:
                            col = cols[0]
                            ids = cols[1:]
                            comp = res
                            found = True
                if not found:
                    raise WrongInputError("Column is not contained " +
                                          "in the resultset")
            else:
                comp = cols[0]
                col = cols[1]
                ids = cols[2:]
            name = self.names[0]
            if not self.out[name]:
                self.out[name] = []
            try:
                self.out[name].append(results[comp][col])
            except:
                raise WrongInputError("Column is not contained " +
                                      "in the resultset")
            for name, col in zip(self.names[1:], ids):
                if not self.out[name]:
                    self.out[name] = []
                self.out[name].append(col)


class AggregatingReceive(Receive, Aggregate):
    """
    A composition of the ``Receive`` and ``Aggregate`` filter.
    """
    inputs = Types(('environment', dict))

    def __init__(self, *args):
        Aggregate.__init__(self, *args)
        Receive.__init__(self)

    def _run(self, **kwargs):
        Receive._run(self, **kwargs)
        results = self.out['results']
        self.out.clear()
        Aggregate._run(self, results=results)


class CondensingReceive(Receive, Condense):
    """
    A composition of the ``Receive`` and ``Condense`` filter.
    """
    inputs = Types(('environment', dict))

    def __init__(self, data, names):
        Condense.__init__(self, data, names)
        Receive.__init__(self)

    def _run(self, **kwargs):
        Receive._run(self, **kwargs)
        results = self.out['results']
        self.out.clear()
        Condense._run(self, results=results)


class Map(Filter):
    """
    Returns a list constructed by applying a filter to all
    elements in the given list.
    """
    inputs = Types(('values', list))
    outputs = Types(('result', list))

    def __init__(self, filter_):
        super(Map, self).__init__()
        self.filter = filter_
        self.names = filter_.inputs.descriptions

    def _run(self, **kwargs):
        values = kwargs['values']
        print values
        self.out['result'] = []
        for v in values:
            param = {self.names.keys().pop(): v}
            self.filter._run(**param)
            self.out['result'].extend(self.filter.out.values())
            self.filter.out.clear()


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
        env = kwargs.pop('environment')
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
    inputs = Types(('data', str))

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
           and kwargs['environment']['current_composition'] is not None:
            node_setting = kwargs['environment']['current_composition'].node_setting
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
    inputs = Types(('filename', str))

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
           and kwargs['environment']['current_composition'] is not None:
            node_setting = kwargs['environment']['current_composition'].node_setting
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
    inputs = Types(('paths', list, str))
    outputs = Types(('data', list, str))

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
    inputs = Types(('singleton', list))
    outputs = Types()

    def __init__(self, name):
        super(Unpack, self).__init__()
        self.name = name

    def _run(self, **kwargs):
        singleton = kwargs['singleton']
        print singleton
        if len(singleton) != 1:
            raise WrongInputError('The list has more than one element.')
        value = singleton.pop()
        self.outputs = Types((self.name, type(value)))
        self.out[self.name] = value


class Mean(Filter):
    """
    Computes the mean of given values.

    Inputs:
    - ``values``: numeric values

    Outputs:
    - ``mean``: mean of the numeric values
    """
    inputs = Types(('values', list))
    outputs = Types(('mean', float))

    def __init__(self):
        super(Mean, self).__init__()

    def _run(self, **kwargs):
        self.out['mean'] = numpy.average(kwargs['values'])


class StandardDeviation(Filter):
    """
    Computes the standard deviation of given values.

    Inputs:
    - ``values``: numeric values

    Outputs:
    - ``standard_deviation``: mean of the numeric values
    """
    inputs = Types(('values', list))
    outputs = Types(('standard_deviation', float))

    def __init__(self):
        super(StandardDeviation, self).__init__()

    def _run(self, **kwargs):
        self.out['standard_deviation'] = numpy.std(kwargs['values'])

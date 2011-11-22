#!/usr/bin/env python

import subprocess
import shlex

import dacapo_analyzer

def benchmark_analyzer(benchmark):
    """
    Return analyzer for :param:`benchmark`.

    :param benchmark: benchmark that will be analyzed
    :returns: function that analyzes the benchmark
    :rtype: function
    """
    if benchmark in dacapo_analyzer.BENCHMARKS:
        return dacapo_analyzer.dacapo_wallclock

def run_benchmark(jvm, benchmark, options=[]):
    """
    Run :param:`benchmark` on :param:`jvm`.

    :param jvm: path to jvm
    :param benchmark: benchmark to execute
    :param options: list of jvm options
    """
    call = ' '.join((jvm, ' '.join(options), benchmark))
    proc = subprocess.Popen(shlex.split(call), stderr=subprocess.PIPE)
    proc.wait()
    _, out = proc.communicate()
    analyzer = benchmark_analyzer(benchmark)
    filtered = analyzer(out)
    send_data(filtered)

def send_data(filtered_output):
    """
    Send filtered benchmark output to server.

    :param filtered_output: relevant benchmark output
    """
    # XXX: testing stub
    print filtered_output

if __name__ == '__main__':
    dacapo_jar = '/home/cofi/Downloads/dacapo-9.12-bach.jar'
    run_benchmark('java', 'fop', ['-jar ' + dacapo_jar])

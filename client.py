#!/usr/bin/env python

""" Executes benchmarks and filters generated data. """

import subprocess

import analyzers

def send_data(filtered_output):
    """
    Send filtered benchmark output to server.

    :param filtered_output: relevant benchmark output
    """
    # XXX: testing stub
    print filtered_output

def run_benchmark(jvm, benchmark, options=[], send_function=send_data):
    """
    Run :param:`benchmark` on :param:`jvm`.

    :param jvm: path to jvm
    :param benchmark: benchmark to execute
    :param options: list of jvm options
    """
    call = [jvm] + options + [benchmark]
    proc = subprocess.Popen(call, stderr=subprocess.PIPE)
    proc.wait()
    _, out = proc.communicate()
    analyzer = analyzers.get_analyzer(benchmark)
    filtered = analyzer(out)
    send_function(filtered)

if __name__ == '__main__':
    def send_stub(filtered_output):
        print filtered_output

    dacapo_jar = 'dacapo-9.12-bach.jar'
    run_benchmark('java', 'fop',
                  options=['-jar', dacapo_jar],
                  send_function=send_stub)

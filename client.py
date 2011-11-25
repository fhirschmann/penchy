#!/usr/bin/env python

""" Executes benchmarks and filters generated data. """

import subprocess

import rpyc

import analyzers

def send_data(filtered_output, server):
    """
    Send filtered benchmark output to server.

    :param filtered_output: relevant benchmark output
    :param server: server identifier, tuple of (Host, Port), if Port is None
                   default will be used
    """
    host, port = server
    conn =  rpyc.classic.connect(host, port) if port is not None \
            else \
            rpyc.classic.connect(host)
    conn.modules.penchy.server.rcv_data(filtered_output)

def run_benchmark(jvm, benchmark, server, options=[], send_function=send_data):
    """
    Run :param:`benchmark` on :param:`jvm`.

    :param jvm: path to jvm
    :param benchmark: benchmark to execute
    :param server: server identifier, see `send_data`
    :param options: list of jvm options
    """
    call = [jvm] + options + [benchmark]
    proc = subprocess.Popen(call, stderr=subprocess.PIPE)
    proc.wait()
    _, out = proc.communicate()
    analyzer = analyzers.get_analyzer(benchmark)
    filtered = analyzer(out)
    send_function(filtered, server)

if __name__ == '__main__':
    def send_stub(filtered_output, _):
        print filtered_output

    dacapo_jar = 'dacapo-9.12-bach.jar'
    run_benchmark('java', 'fop', ("192.168.56.11", 4343),
                  options=['-jar', dacapo_jar],
                  send_function=send_stub)

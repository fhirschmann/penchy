========================
Job Description Language
========================

Here is a simple Job::

    # A job description is two part: part 1 introduces the involved elements and
    #                                part 2 joins them in a job

    # part 1: introduce the elements
    # setup job environment
    from penchy.jobs import *

    # define a node
    node = NodeConfiguration(
        # that is the localhost
        'localhost',
        # ssh port is 22
        22,
        # the executing user is the current one
        os.environ['USER'],
        # we execute in /tmp
        '/tmp',
        # all jvm are specified relative to /usr/bin
        '/usr/bin')

    # define a jvm with relative path java
    jvm = jvms.JVM('java')
    # you can also specify an absolute path:
    # jvm = jvms.JVM('/usr/java')

    # fuse jvm and node
    jconfig = makeJVMNodeConfiguration(jvm, node,
                                       # and give it a decorative name (optional)
                                       name="Simple Example!")

    # setup a workload
    w = workloads.ScalaBench('dummy')
    # and add it the the jvms that should execute it
    jvm.workload = w

    # setup filter, used in flows
    f1 = filters.DacapoHarness()
    f2 = filters.Print()

    # part 2: form elements to a job
    job = Job(
        # setup the JVMNodeConfigurations that are included, can be a single one or
        # a list of configurations
        configurations=jconfig,
        # specify the flow of data on clients
        client_flow=[
            # flow from Scalabench workload to DacapoHarness filter
            Edge(w, f1,
                 # and match filter inputs to workload outputs (here with same name)
                 [('stderr', 'stderr'),
                  ('exit_code', 'exit_code')]),
            # flow from ScalaBench workload to Print filter
            Edge(w, f2,
                 # and feed stderr and exit_code output prefix with 'workload_' to filter
                 [('stderr', 'workload_stderr'),
                  ('exit_code', 'workload_exit_code')]),
            # feed whole output of DacapoHarness filter to print filter (with the name of the output)
            Edge(f1, f2)
        ],
        # there is no flow on the server side
        server_flow=[],
        # jvms will be run twice
        invocations = 2
    )

    # a nice trick: check the job for plausibility if run as ``python <jobname>``
    if __name__ == '__main__':
        job.check()


JVM
===

Workloads
=========

Tools
=====

Agent
-----

WrappedJVM
----------

Filter
======

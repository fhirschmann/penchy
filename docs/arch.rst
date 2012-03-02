============
Architecture
============

Job
===

Pipeline
========

.. graphviz::

    digraph Classes {
        rankdir = BT
        node [shape=box]
        edge [arrowhead = empty]

        Tool -> NotRunnable
        Tool -> PipelineElement

        Filter -> PipelineElement
        SystemFilter -> Filter
        Plot -> Filter

        Workload -> NotRunnable
        Workload -> PipelineElement

        WrappedJVM -> JVM
        WrappedJVM -> PipelineElement

    }

Pipeline-Dependencies
---------------------

Input/Output Validation
-----------------------

Execution and Communication Process
===================================

PenchY uses XML-RPC in order to communicate between clients, hereafter
called nodes to distinguish physical machines from the PenchY client.

Upon executing a job, PenchY will follow a procedure to distribute your wishes
as defined in your job. This procedure will now be explained in detail.

1. Distributing jobs to all involved nodes
------------------------------------------

When you execute PenchY, it will first copy the following files to your nodes:

1. The Bootstrap Client (``penchy_bootstrap``)
2. A Maven POM file listing the dependencies of your job (``bootstrap.pom``)
3. Your configuration file (``config.py``)
4. The job file itself

This will be accomplished by using SCP.

2. Executing the Bootstrap Client
---------------------------------

The next step in the process is to execute the bootstrap client, which was
previously uploaded to all nodes. This is done by simply using SSH.

In addition to installing the PenchY client from a maven repository,
the bootstrap client will install all maven dependencies required
by the current job.

3. Executing the Client
-----------------------

Next up: the PenchY client. Installed from a maven repository, it will
get started by the bootstrap client.

The client is responsible for the actual execution of the job.

4. Reporting Results
--------------------

Once the client has finished what it was made for, it will report
the results back to the server. Please note that it is absolutely
probable that the client will report to the server multiple times
within a single job. This is due to the architecture of PenchY,
where the nodes execute one or more :class:`~penchy.jobs.job.SystemComposition`
in a single job.

============
Architecture
============

Job
===

A job is a full fledged Python module (even though it has an ``.job``
extension) and gives you the power of the whole Python language: you can import modules or execute
programs.
This provides a high degree of flexibility for the user.
There are no restrictions on the language, but because the job is shared by
server and clients it has to be executable on the server and the clients.

Communication with the rest of PenchY happens via the Job Description Language (JDL)
API.
The JDL is located in the directory :file:`penchy/jobs/` and the parts of it
that are exposed (and useful) to the user are listed in the file
:file:`penchy/jobs/__init__.py`.

The design of the JDL had two main priorities: To make writing jobs ease and to
make it easy to extend.

The first priority is the reason why you can connect parts of it by using the
``>>`` syntax.

The second priority is the cause of inheritance hierarchy of the JDL (you can
see it below).
In Python it is common practice not to rely on types or classes to encode
the behavior of an object but to use protocols [#]_.
We decided that it makes extension easier and furthers uniformity to make this
behavior explicit.
Furthermore: We can relieve extension writers from common tasks.

Pipeline
========

Here is a diagram that shows the inheritance hierarchy of the JDL:

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

The elements of the Pipeline provide output (under logical names) that can be
selected (full or in part) by other elements as input.
Such an output can be used by several elements and must be persistant because of
this (don't use generators!).
Analogously many outputs can be used the input of an element.

The output is produced when ``run`` is called on an element and likewise fed to
``run`` of the element that needs this output.

Every element (not just :class:`~penchy.jobs.elements.PipelineElement`) has
support for hooks that provide methods for ``setup`` and ``teardown`` methods.
The execution of ``run`` is surrounded by those two, i.e. ``setup`` is executed
at the beginning of ``run`` and ``teardown`` at the end.
Tools and Workloads are not run, but they have hooks nevertheless.
Those hooks are executed when their :class:`~penchy.jobs.jvms.JVM` is run.

Pipeline-Dependencies
---------------------

Pipeline-Dependencies happen in the flow of a
:class:`~penchy.jobs.job.SystemComposition` and in the (server-)flow of a
:class:`~penchy.jobs.job.Job` in form of data dependencies.

Data dependencies in the job are expressed via
:class:`~penchy.jobs.dependency.Edge` objects.
A user never encounters those because of the ``>>`` syntax, which generates
:class:`~penchy.jobs.dependency.Pipeline` objects, but they are used internally.
:class:`~penchy.jobs.dependency.Pipeline` can be converted to Edges by
accessing their ``edges`` attribute.

The Edges construct a DAG (Directed Acyclic Graph) that is turned into a
execution order by a topological sort (performed by
:func:`~penchy.jobs.dependency.edgesort`).
The elements are then executed one after another in this order.

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

This will be accomplished by using SSH.

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

.. [#] (e.g. a object is seen as a file if it has the attributes and methods of
       a file, not only if it is a subclass of file).

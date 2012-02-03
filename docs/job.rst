============
Writing Jobs
============

Here is a simple Job:

.. _sample-job:
  .. literalinclude:: commented_sample_job.py
        :language: python
        :linenos:
        :encoding: utf8


The two main responsibilities of a job are

    1. describe what should be executed by the JVMs and on which nodes
    2. describe what to do with the results of the execution

The second is the flow (or sometimes called the pipeline).

Defining the flow
=================

Every :class:`~penchy.jobs.elements.PipelineElement` has the attributes ``inputs``
and ``outputs``.
They describe how inputs (and outputs) are named and of which type they are.

The flow is a description of how the data flows from outputs to inputs. In other
words: How Elements depend on each other for data.

The inputs of :class:`~penchy.jobs.elements.PipelineElement` have to be
completely saturated for a valid flow.

In the following ``e1`` and ``e2`` are just some
:class:`~penchy.jobs.elements.PipelineElement`.

The basic syntax
----------------

In the following section, there is a short introduction on what syntax you
can use to define dependencies between elements and what data they comprise of.
It is used to define the ``client_flow`` and ``server_flow`` for a
:class:`~penchy.jobs.job.Job`.

.. warning::

   You have to be careful while defining the flow because the types encode the
   meaning to the pipeline. This is valid::

     e1 >> [('a', 'b')] >> e2

   while this is not::

     e1 >> (('a', 'b')) >> e2

Mapping outputs to inputs
~~~~~~~~~~~~~~~~~~~~~~~~~

To pass the output ``a`` of ``e1`` to the ``b`` input of ``e2`` use::

  e1 >> ('a', 'b') >> e2

to additionally pass ``c`` to ``d``, it becomes::

  e1 >> [('a', 'b'), ('c', 'd')] >> e2

In case output and input are named the same you can use::

  e1 >> ['a', 'b'] >> e2

and it will pipe the outputs ``a`` and ``b`` of ``e1`` to the inputs ``a`` and
``b`` of ``e2``.

The last method is for piping one output to an input with the same name::

  e1 >> 'a' >> e2

this pipes the output ``a`` of ``e1`` to the input ``a`` of ``e2``.

Passing everything
~~~~~~~~~~~~~~~~~~

To pass everything you can simply use the syntax::

  e1 >> e2

but you have to keep in mind two things:

 * All outputs of ``e1`` are passed to ``e2``. Therefore, it is necessary that
   both, outputs of ``e1`` and inputs of ``e2`` have the same names and types.
 * If ``e1`` has more outputs than ``e2`` inputs, warnings will occur. In this
   case, please read on in order to learn how to remove the superfluous
   outputs.

Cutting outputs down
~~~~~~~~~~~~~~~~~~~~

If ``e1`` and ``e2`` have compatible inputs and outputs, but ``e2`` needs fewer
input than ``e1`` offers outputs, you can use the following syntax (already introduced
above)::

  e1 >> ['a', 'b'] >> e2

in order to explicitly name the input and outputs you want to work with.

Let's assume ``e1`` has the outputs ``a``, ``b``, ``c`` and ``e2`` is only
accepting the first two outputs, then PenchY will produce warnings if you were
to write::

  e1 >> e2

However, you can omit these warnings by specifying the inputs and outputs
explicitly as explained above.

Defining multiple pipelines
---------------------------

To define multiple pipeline in the flows you just add more.
Here we define two lines of action in the client flow (analogous for the server
flow)::

  job = Job(...
            client_flow=[
                e1 >> e2 >> e3,
                e1 >> e4
            ]
            ...
            )

Survey of the elements
======================

Besides :class:`~penchy.jobs.dependency.Edge`, there are other elements of a
job.
This chapter tries to give an overview of what they are and how they are used.
For an in-depth treatment see the :ref:`Job API <job-api>`.

NodeSetting
-----------
A :class:`~penchy.jobs.job.NodeSetting` describes how to access a node and its
properties.

For details on accessing see the API documentation of :class:`~penchy.jobs.job.NodeSetting`.

There are two kinds of properties:
 * The first is used to check a job for plausibility (see below).
 * The second is descriptive and for human eyes.

The second may contain attributes such as a textual description of the Node's
features, CPU type, performance or amount of RAM, or whatever you deem helpful.

JVM
---

:class:`~penchy.jobs.jvms.JVM` is an abstraction of Java Virtual Machines and executes its :ref:`Workload <sec-workloads>`.
It may contain an :ref:`Agent <sec-agent>`.

You can specify options like you would on a shell (including a classpath). These
will be passed to the JVM. Here's an example with several options::

  j = JVM('java', '-verbose:gc -Xmx800m -Xms42m')

JVMs may contain pre- and post-hooks, which are executed before
and after they are run, respectively.

.. _sec-workloads:
Workloads
---------

Workloads are programs (mostly benchmarks) that are executed by a JVM.

Workloads may contain pre- and post-hooks, which are executed before
and after they are run, respectively.

Tools
-----

Tools are programs that collect data about the executed workload and come in two
flavors: Agent and WrappedJVM.

Tools may contain pre- and post-hooks, which are executed before
and after they are run, respectively.

.. _sec-agent:
Agent
~~~~~

An Agent is a Tool that is invoked via the JVM's agent parameters (e.g.
``-agentlib``).
It is used as an attribute for a JVM and collects data about the workload also
set for this JVM. For example, in::

  j = JVM('java')
  j.workload = Dacapo('fop')
  j.tool = HProf('')

:class:`~penchy.jobs.tools.HProf` will collect data about the ``fop`` benchmark of the
:class:`~penchy.jobs.workloads.Dacapo` benchmark suite.


WrappedJVM
~~~~~~~~~~

A WrappedJVM on the other hand is itself a program that calls the desired JVM
and is used instead of a JVM but accepts the same arguments (if not more).

An example for a WrappedJVM is :class:`~penchy.jobs.jvms.ValgrindJVM` (and its
subclasses).
They setup a normal JVM but instead of calling it directly they pass it to
Valgrind for execution.

Filter
------

Filters are used to process the raw output of the tools. They define the
client and server flow and therefore describe how the raw output of
(potentially many) Tools is processed into the desired output (e.g. diagrams).

Filters may contain pre- and post-hooks, which are executed before
and after they are run, respectively.

Using penchyrc: Stop repeating yourself
=======================================

To avoid duplication of settings (such as :class:`NodeSetting` or user names)
there is a possibility to use a configuration file (:file:`penchyrc`) and put
frequently used settings there.

The configuration is a Python module and you can use any Python Code there to
configure.
If you do not specify where :file:`penchyrc` is (in the penchy invocation:
``penchy --config <file>``) it will be searched in :file:`$HOME/.penchyrc`.

To use :file:`penchyrc`, you have to import the ``config`` module, the header of
above :ref:`sample job <sample-job>`::

  import os
  from penchy.jobs import *

  node = NodeSetting('localhost', 22, os.environ['USER'], '/tmp', '/usr/bin')

would become this::

  from penchy.jobs import *
  import config

  node = config.LOCALNODE

given a :file:`penchyrc` that looks like this::

  import os
  from penchy.jobs import NodeSetting
  
  LOCALNODE = NodeSetting('localhost', 22, os.environ['USER'], '/tmp', '/usr/bin')

Testing Jobs
============

To avoid bad surprises we offer two methods to test a job without running it
fullscale.

The first is plausibility checking which does a static analysis if a job can run
on the given nodes (availability of JVMs and Tools) and if the pipeline is
saturated and the expected types are delivered.
A successful check does not guarantee that the job will execute fine but
increases the likelihood and catches mistakes early on.

The second is running it locally which actually executes the job but does not
use the network or other nodes.
This also means that its applicability is limited to jobs that are executed on
``localhost`` but can be used as a test balloon for larger jobs.

Checking for plausibility
-------------------------

To check for plausibility you can use ``penchy --check <jobfile>``.
As outlined above it checks for each :class:`~penchy.jobs.job.SystemComposition` if

- the JVMs are present on the nodes (if configured)
- all JVMs have a workload
- components are runable on the node's OS

and for the pipeline if

- each :class:`~penchy.jobs.element.PipelineElement` receives the expected input
  (correct names and types)

Running the job locally
-----------------------

To run the job locally you can use ``penchy --run-locally <jobfile>``.
It will run all :class:`~penchy.jobs.job.SystemComposition` on the ``localhost``
node directly and not via deployment and SSH.

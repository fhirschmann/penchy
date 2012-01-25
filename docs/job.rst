========================
Job Description Language
========================

Here is a simple Job:

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

The flow is a description how the data flows from outputs to inputs. In other
words: How Elements depend on data.

The flow is expressed in terms of a list of :class:`~penchy.jobs.dependency.Edge`.
Each :class:`~penchy.jobs.dependency.Edge` has a ``source``, a ``sink`` and a
description of how to map the output of the ``source`` to the input of the
``sink``.
This description can be missing (or set to ``None``) to implicitly pipe all ``source``
output to ``sink``.
That means that ``sink`` must have a ``inputs`` that is compatible with
``outputs`` of ``source``.
Here is an example::

  w = workloads.ScalaBench('dummy')  # all workloads have stderr, stdout
                                     # and exit_code as output
  f = filters.DacapoHarness()  # This filter only expects stderr and exit_code

  Edge(w, f)  # this works because w and f are compatible, but there will be a
                warning because stdout output of workload will not be used


This description can also be explicitly provided.
A reason can be that ``sink`` and ``source`` are incompatible in the expected
named and their types or to provide only a subset of the outputs.
Here the example from above, that won't show any warnings::

  w = workloads.ScalaBench('dummy')  # all workloads have stderr, stdout
                                     # and exit_code as output
  f = filters.DacapoHarness()  # This filter only expects stderr and exit_code

  Edge(w, f, [('stderr', 'stderr),
              ('exit_code', 'exit_code')])

With :class:`~penchy.jobs.dependency.Edge` you specify a 1:1 relation but within
the whole flow an :class:`~penchy.jobs.elements.PipelineElement` can pass its
output to many :class:`~penchy.jobs.elements.PipelineElement` and also receive
from many.
For Example::

  w = workloads.ScalaBench('dummy')
  f1 = filters.DacapoHarness()
  f2 = filters.Print()

  flow = [Edge(w, f1),  # w passes output to two elements
          Edge(w, f2),  # f2 receives input from two inputs
          Edge(f1, f2)
         ]

Survey of the elements
======================

Besides :class:`~penchy.jobs.dependency.Edge` there are other elements of a
job.
This chapter tries to give what they are and how they are used.
For a in-depth treatment see the :ref:`Job API <job-api>`.

NodeSetting
-----------
A :class:`~penchy.jobs.job.NodeSetting` describes how to access a node and its
properties.

For details on accessing see the API documentation of :class:`~penchy.jobs.job.NodeSetting`.

There are two kinds of properties:
The first are used to check a job for plausibility (see below).
The second are descriptive and for human eyes.

They may contain such things as a textual description of the Node's features
such as CPU type and performance or amount of RAM or whatever you deem helpful.

JVM
---

A JVM is a Java Virtual Machine and executes its Workload.
It may contain an Agent.

You can specify options like you would on a shell (including a classpath) those
will be passed to the JVM. Here is an example with several options::

  j = JVM('java', '-verbose:gc -Xmx800m -Xms42m')

JVMs may contain pre-hooks and post-hooks which are executed before respective
after they are run.

Workloads
---------

Workloads may contain pre-hooks and post-hooks which are executed before respective
after they are run.

Tools
-----

Tools are programs that collect data about the executed workload.
They come in two flavors: Agent and WrappedJVM.

Tools may contain pre-hooks and post-hooks which are executed before respective
after they are run.

Agent
~~~~~

An Agent is a Tool that is invoked via the JVM's agent parameters (e.g.
``-agentlib``).
It is used as an attribute for a JVM and collects data about the workload also
set for this JVM. For example in::

  j = JVM('java')
  j.workload = Dacapo('fop')
  j.tool = HProf('')

will :class:`~penchy.jobs.tools.HProf` collect data about the ``fop`` benchmark of the
:class:`~penchy.jobs.workloads.Dacapo` benchmark suite.


WrappedJVM
~~~~~~~~~~

A WrappedJVM on the other side is itself a program that calls the desired JVM.
It is used instead of a JVM but accepts the same arguments (if not more).

Currently there is no implementation of a WrappedJVM but an example would be to
use Valgrind to analyze the execution of the JVM.

Filter
------

Filter may contain pre-hooks and post-hooks which are executed before respective
after they are run.

Using penchyrc: Stop repeating yourself
=======================================

To avoid duplication of settings (such as :class:`NodeSetting` or user names)
there is a possibility to use a configuration file (:file:`penchyrc`) and put
often used settings there.

The configuration is a Python module and you can use any Python Code there to
configure.
If you don't specify where :file:`penchyrc` is (in the penchy invocation:
``penchy --config <file>``) it will be searched in :file:`$HOME/.penchyrc`

To use :file:`penchyrc` you have to import the ``config`` module, the header of
above sample job::

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

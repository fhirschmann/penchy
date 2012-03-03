============
Writing Jobs
============

We will start off with a simple job, which can also be
found in ``docs/jobs/simple.job``.

.. _sample-job:

  .. literalinclude:: jobs/simple.job
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

In the following section, there is a short introduction on what syntax you can
use to define dependencies between elements and what data they comprise of.
It is used to define the ``flow`` for a
:class:`~penchy.jobs.job.SystemComposition` and ``server_flow`` for a
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

To define multiple pipelines in the flows you just add more to the list of flow.
Here we define two lines of action in the
:class:`~penchy.jobs.job.SystemComposition` flow (analogous for the server
flow)::

  ...
  compososition.flow = [
                e1 >> e2 >> e3,
                e1 >> e4
            ]
  ...

Multiple Workloads & Flows
--------------------------

A :class:`~penchy.jobs.job.SystemComposition` comprises of a JVM (with its
``workload`` and ``tool``) that describes what to execute and a
:class:`~penchy.jobs.job.NodeSetting` that describes where to execute it.
In addition, the flow describes how to process the results of the execution.
Using multiple workloads means using multiple
:class:`~penchy.jobs.job.SystemComposition` with different
:class:`~penchy.jobs.jvms.JVM` (the number of compositions on a node is not
limited). Here is an example of two different workloads::

  j1 = JVM('java')
  j2 = JVM('java')
  c1 = SystemComposition(j1, LOCALNODE)
  c2 = SystemComposition(j2, LOCALNODE)

  w1 = Dacapo('fop')
  j1.workload = w1
  w2 = ScalaBench('scalac')
  j2.workload = w2

And now we will add two different flows::

  c1.flow = w1 >> filters.DacapoHarness() >> filters.Print()
  c2.flow = w2 >> filters.DacapoHarness() >> filters.Dump() >> filters.Print()

:class:`~penchy.jobs.elements.PipelineElement` can be used across flows but will be
reset after the execution of a :class:`~penchy.jobs.job.SystemComposition`.
This is why we could reuse the ``filters.DacapoHarness()`` above
(``filters.Print()`` has no state to speak of) without trouble::

  h = filters.DacapoHarness()
  c1.flow = w1 >> h >> filters.Print()
  c2.flow = w2 >> h >> filters.Dump() >> filters.Print()

Survey of the elements
======================

Besides the definition of the flow, there are other elements to a job.
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

JVMs may contain hooks, which are executed before and after they are run.
Please consult the section on :ref:`using hooks <using-hooks>`.

.. _sec-workloads:

Workloads
---------

Workloads are programs (mostly benchmarks) that are executed by a JVM.

Workloads may contain hooks, which are executed before and after they are run.
Please consult the section on :ref:`using hooks <using-hooks>`.

Tools
-----

Tools are programs that collect data about the executed workload and come in two
flavors: Agent and WrappedJVM.

Tools may contain hooks, which are executed before and after they are run.
Please consult the section on :ref:`using hooks <using-hooks>`.

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

Filters may contain hooks, which are executed before and after they are run.
Please consult the section on :ref:`using hooks <using-hooks>`.

Using penchyrc: Stop repeating yourself
=======================================

To avoid duplication of settings (such as :class:`penchy.jobs.job.NodeSetting` or user names),
there is a possibility to use a configuration file (:file:`penchyrc`), and put
frequently used settings there.

The configuration is a Python module, and you can put any Python code there.
If you do not specify where :file:`penchyrc` is located (in the penchy invocation:
``penchy --config <file>``), it will be assumed to be in :file:`$HOME/.penchyrc`.

To use :file:`penchyrc`, you have to import the ``config`` module. The header of
the :ref:`sample job <sample-job>` above::

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

Defining Timeouts
=================

PenchY allows the definition of timeouts in order to automatically
terminate JVMs. These timeouts can be defined in your job like so::

    node = NodeSetting(..., timeout_factor=2)
    jvm = jvms.JVM=(..., timeout_factor=3)
    jvm.workload = workloads.ScalaBench(..., timeout=5)

where the workload defines an absolute timeout value and the other
two add the possibility to add a factor which will get multiplied
with the workload timeout.

.. warning::

    It is very important to understand that these timeouts are defined
    per execution of the JVM.

    Let's say your timeout is 10 seconds, than a Scalabench run with
    4 iterations may not exceed 10 seconds in total.

    However, when Scalabench is asked to run 10 invocations, these
    invocations should **each** not take longer than 10 seconds.

Before the exeuction of the JVM, the PenchY client will ask the server
to start a timeout, after which it should step in and remotely terminate
the JVM. Once the JVM has finished what it was asked to, the client
will ask the server to stop the timeout again. This process is repeated
for every run of the JVM.

.. note::

    Timeouts do not affect any filters you might want to use. When
    your filters don't terminate, the timeout won't terminate them
    either.

.. _using-hooks:

Using Hooks
===========

PenchY allows the definition of hooks which can execute an arbitrary
command before and after the execution of a JVM. In general, a Hook
will execute two functions, ``setup`` and ``teardown``, which will
be execute before and after the JVM run, respectively.

There are two ways to define these hooks:

Simple Declaration
------------------

In simple cases where you want to execute a single command, PenchY
provides a convenience method::

    jvm = JVM('java')
    jvm.hooks.append(Hook(setup=lambda: dosomething(),
                          teardown=lambda: dosomething()))

Using this method, you can write simple hooks that will, for instance,
delete files you might have created in your benchmark run.

Advanced Declaration
--------------------

In cases where you need more control, you can subclass
:class:`~penchy.jobs.hooks.BaseHook` like so::

    jvm = JVM('java')
    class MyHook(hooks.BaseHook):
        def setup(self):
            # do something
            pass

        def teardown(self):
            # do something
            pass

    myhook = MyHook()
    jvm.hooks.append(myhook)

This will give you the most power over the definition of actions which
should take place before and after the execution of a JVM.

Execution Hook
--------------

PenchY comes with :class:`~penchy.jobs.hooks.ExecuteHook`, which is
a simple Hook that is supposed to make the exeuction of programs
easier. It allows you to pass a command along with it's arguments,
which will get started before the exeuction and terminated afterwards
(if neccessary)::

    jvm = JVM('java')
    myhook = hooks.ExecuteHook('myprogram')
    jvm.hooks.append(myhook)

Upon teardown, the returncode will be checked. If the program has
not terminated yet, the Hook itself will terminate it.

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

To check for plausibility, you can use ``penchy --check <jobfile>``.
As outlined above, it checks for each :class:`~penchy.jobs.job.SystemComposition` if

- the JVMs are present on the nodes (if configured)
- all JVMs have a workload
- components are runable on the node's OS

and for the pipeline if

- each :class:`~penchy.jobs.elements.PipelineElement` receives the expected input
  (correct names and types)

Running the job locally
-----------------------

To run the job locally, you can use ``penchy --run-locally <jobfile>``.
It will run all :class:`~penchy.jobs.job.SystemComposition` on the ``localhost``
node directly and not via deployment and SSH.

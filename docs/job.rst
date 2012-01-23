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

The second is the flow.

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

NodeConfiguration
-----------------

JVM
---

Workloads
---------

Tools
-----

Agent
~~~~~

WrappedJVM
~~~~~~~~~~

Filter
------

Using penchyrc: Stop repeating yourself
=======================================


Testing Jobs
============

Checking for plausibility
-------------------------

Running the job
---------------

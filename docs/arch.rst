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

        Workload -> NotRunnable
        Workload -> PipelineElement

        WrappedJVM -> JVM
        WrappedJVM -> PipelineElement

    }


Client
======

Server
======

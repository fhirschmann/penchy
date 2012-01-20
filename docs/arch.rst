Architecture
============

Write me!

.. graphviz::

    digraph Classes {
        JVM -> WrappedJVM;
        PipelineElement -> Tool;
        PipelineElement -> Workload;
        PipelineElement -> Filter;
        PipelineElement -> WrappedJVM;
        NotRunnable -> Workload;
        NotRunnable -> Tool;
    }

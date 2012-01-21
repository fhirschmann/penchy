Architecture
============

Write me!

.. graphviz::

    digraph Classes {
        JVM -> WrappedJVM;
        PipelineElement -> Tool;
        PipelineElement -> Workload;
        PipelineElement -> Filter;
        Filter -> SystemFilter;
        PipelineElement -> WrappedJVM;
        NotRunnable -> Workload;
        NotRunnable -> Tool;
    }

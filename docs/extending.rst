.. _extending:

====================================================
 Extending the Pipeline -- Writing PipelineElements
====================================================

General notes
=============

**Each and Every** :class:`~penchy.jobs.elements.PipelineElement` has to follow what is
described here.

A :class:`~penchy.jobs.elements.PipelineElement` has these attributes:

- ``out``, a ``defaultdict(list)`` (which means that if you access a key that is
  not in use, you will be presented a list for use)
- ``inputs``, a :class:`~penchy.jobs.typecheck.Types`
- ``outputs``, a :class:`~penchy.jobs.typecheck.Types`

and this methods:

- ``_run``, which takes arbitrary keyword arguments and performs the actual action.

``out`` is used to offer the output of this
:class:`~penchy.jobs.elements.PipelineElement` to the rest of the Pipeline. You
can choose to ignore the ``defaultdict(list)`` nature of it, and replace it by a
:class:`dict` or by an object that behaves like a :class:`dict`.

What is part of the interface that offer via ``out`` has to be described by
``outputs``.
This can be set at class level and thus used for all instances of the
:class:`~penchy.jobs.elements.PipelineElement` you define, or overridden (or even
created) in every instance (likely by ``__init__`` or ``_run``, see below).

If you only offer the output ``out`` which is a :class:`list` of :class:`list`
of :class:`int`, you will use this::

    class YourElement(PipelineElement):
        ...
        outputs = Types(('out', list, list, int))
        ...

You can nest this type description arbitrarily deep, but this makes only sense
if you use collection-natured types (such as lists or tupels).
For :class:`dict`, you describe the types of the values; keys won't be checked.

``outputs`` is used to create the flow from a Source to a Sink if you don't
explicitly map the outputs to the inputs (that is, use the ``Sink >> Source``
syntax).
In this case, ``outputs`` has to be set at the latest after ``_run`` has been
called.
The types of ``outputs`` are only relevant at check time, where PenchY
statically examines if Sinks and Sources fit into each other.
That means if the outputs are only known after the execution, you should not
bother to set the exact types.
A ``Types(('first', object), ('second', object), ...)`` is sufficient and will
do the same.

``inputs`` are declared in the same way as ``outputs``.
They are relevant at check time and execution time.
At execution time, the values of the actual items passed to ``_run`` are checked,
not the ``outputs`` descriptions of the Sources that passed the items.
As they are relevant at the beginning of ``_run``, they have to be set at the latest
when the element is initialized, that is in the ``__init__`` method.

Additionally to the types of ``inputs`` and ``outputs``, you should describe
(e.g. in the docstring of the class) which ``inputs`` and ``outputs`` exist and
what they mean.

``_run`` performs the execution of the element, and you are free to do want you
want here.
With two exceptions:

1. the signature is ``def _run(self, **kwargs)`` and nothing else (well you can
   change the name of ``kwargs``)
2. you set ``out`` to the values that are described in ``outputs``


If you define elements that are only intended for server usage and require
libraries, you should not import them toplevel but at the filter level (that is,
in ``__init__``, or similar) to minimize the libraries needed for a client.
This is necessary because every client reads the complete job (and therefor the
complete job description language).

Workloads
=========

A workload has the attributes (you may want to use properties instead):

- ``arguments`` the arguments to execute the workload
- (optional) ``information_arguments`` the arguments to gather information about
  the workload (version, etc.)

You don't have to set ``out`` yourself as it will be set by the executing JVM.
The same goes for ``outputs``, because they are set by
:class:`~penchy.jobs.elements.Workload` and inherited (if you change them, you
have to provide a strict superset).

Filters
=======

Filters can be a normal :class:`~penchy.jobs.elements.Filter` or
:class:`~penchy.jobs.elements.SystemFilter`.
The latter will be passed an additional argument called ``:environment:`` on
execution, which describes the execution environment of the SystemFilter (see
:meth:`penchy.jobs.job.Job._build_environment`).

Tools
=====

Agents
------

An Agent is a :class:`~penchy.jobs.elements.Tool` that is invoked via the JVM's
agent parameters (e.g.  ``-agentlib``).
Contrary to a workload, it has to care for its ``outputs`` and ``out``.

An Agent has to provide these attributes (here you might want to use properties as well):

- ``arguments`` the arguments to execute the agent, that is to include it in the JVM

WrappedJVM
----------

A WrappedJVM is a :class:`~penchy.jobs.elements.PipelineElement` as well as a
:class:`~penchy.jobs.jvms.JVM`.
You have to provide these attributes:

- ``cmdline`` how to invoke the JVM with the wrapping (to use most of
  :class:`~penchy.jobs.jvms.JVM` infrastructure)

and these methods:

- ``information`` that returns information about the JVM (and its configuration)

Even if a WrappedJVM is a :class:`~penchy.jobs.elements.PipelineElement`, you
must not specify a ``_run`` method.

Whatever you do: You must behave like a :class:`~penchy.jobs.jvms.JVM`, so be
sure to take a look how it is implemented.

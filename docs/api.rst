===
API
===

.. _job-api:

Job Description
===============

Jobs
----
.. automodule:: penchy.jobs.job

JVMs
----
.. autoclass:: penchy.jobs.jvms.JVM

Workloads
---------
.. automodule:: penchy.jobs.workloads

Tools
-----
.. automodule:: penchy.jobs.tools

Filters
-------
.. automodule:: penchy.jobs.filters

Pipeline dependency specification
---------------------------------

.. autoclass:: penchy.jobs.dependency.Edge
.. automethod:: penchy.jobs.dependency.Edge.__rshift__

.. autoclass:: penchy.jobs.dependency.Pipeline
.. automethod:: penchy.jobs.dependency.Pipeline.__rshift__

Elements of the Pipeline
------------------------
.. automodule:: penchy.jobs.elements
.. autoclass:: penchy.jobs.jvms.WrappedJVM

Uncategorized
=============
TODO: CATEGORIZE ME

Client
------
.. automodule:: penchy.client

Maven
-----
.. automodule:: penchy.maven

Nodes
-----
.. automodule:: penchy.node

Server
------
.. automodule:: penchy.server

Internal
========

Utilities
---------
.. automodule:: penchy.util

Pipeline dependency resolution
------------------------------
.. automodule:: penchy.jobs.dependency

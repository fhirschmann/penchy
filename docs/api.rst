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

Hooks
-----
.. automodule:: penchy.jobs.hooks

Workloads
---------
.. automodule:: penchy.jobs.workloads

Tools
-----
.. automodule:: penchy.jobs.tools

Filters
-------
.. automodule:: penchy.jobs.filters

Plots
-----
.. automodule:: penchy.jobs.plots

Type checking
-------------
.. automodule:: penchy.jobs.typecheck

Pipeline dependency specification
---------------------------------

.. autoclass:: penchy.jobs.dependency.Edge
.. automethod:: penchy.jobs.dependency.Edge.__rshift__

.. autoclass:: penchy.jobs.dependency.Pipeline
.. automethod:: penchy.jobs.dependency.Pipeline.__rshift__


Maven Dependencies
------------------

.. autoclass:: penchy.maven.MavenDependency

Elements of the Pipeline
------------------------
.. automodule:: penchy.jobs.elements
.. autoclass:: penchy.jobs.jvms.WrappedJVM

Communication
=============

Client
------
.. automodule:: penchy.client

Nodes
-----
.. automodule:: penchy.node

Server
------
.. automodule:: penchy.server

Maven
=====
.. automodule:: penchy.maven

Internal
========

Utilities
---------
.. automodule:: penchy.util

Pipeline dependency resolution
------------------------------
.. autofunction:: penchy.jobs.dependency.edgesort
.. autofunction:: penchy.jobs.dependency.build_keys

Maven
=====
.. autofunction:: penchy.maven.get_classpath
.. autofunction:: penchy.maven.setup_dependencies
.. autoclass:: penchy.maven.POM
.. autoclass:: penchy.maven.MavenError
.. autoclass:: penchy.maven.IntegrityError
.. autoclass:: penchy.maven.POMError
.. autoclass:: penchy.maven.BootstrapPOM
.. autoclass:: penchy.maven.PenchyPOM
.. autofunction:: penchy.maven.make_bootstrap_pom
.. autofunction:: penchy.maven.write_penchy_pom

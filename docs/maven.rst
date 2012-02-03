Maven Documentation
===================
PenchY is using Maven to handle dependencies which Workloads
might have.

Declaring Maven Dependencies
----------------------------
Maven dependencies can be declared using the `MavenDependeny` module:

.. autoclass:: penchy.maven.MavenDependency

If you want to write, for example, a Workload named `Dacapo` which depends
on the dacapo benchmark suite, you'd simply declare its dependencies
as a class attribute like so::

    class Dacapo(Workload):
        DEPENDENCIES = set((MavenDependency(...),)

Once the dependencies have been declared, they will be collected and
installed on the nodes via maven pom files which are automatically
produced on all nodes.

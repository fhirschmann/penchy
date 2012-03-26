Maven
=====

PenchY is using `Maven <http://maven.apache.org>`_
in order to distribute the client and its
dependencies. You can find the corresponding Maven Project Object
Models in the :file:`mvn` subdirectory of the PenchY distribution.

The PenchY client is deployed as a zip file built by the
`Maven Assembly Plugin <http://maven.apache.org/plugins/maven-assembly-plugin/>`_
when you execute `mvn deploy` in :file:`mvn/penchy`. The
`descriptor <http://maven.apache.org/plugins/maven-assembly-plugin/assembly.html>`_
is located in :file:`mvn/penchy/descriptor.xml` and lists the files which are going
to be included in the zip file.

Deploying PenchY via Maven
--------------------------
If you wish to host PenchY on your own server, you need to
edit :file:`mvn/penchy/pom.xml` and set the `id` in of your
maven repository server accordingly.

Let's assume your :file:`~/.m2/settings.xml` defines a server
`mysite`::

    <settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
        http://maven.apache.org/xsd/settings-1.0.0.xsd">
        <localRepository/>
        <interactiveMode/>
        <usePluginRegistry/>
        <offline/>
        <pluginGroups/>
        <servers>
            <server>
                <id>mysite</id>
                <username>bp</username>
                <privateKey>${env.HOME}/.ssh/id_rsa</privateKey>
                <filePermissions>664</filePermissions>
                <directoryPermissions>775</directoryPermissions>
            </server>
        </servers>
    </settings>

Then you'd have to modify :file:`penchy/mvn/pom.xml` and set the
server `id` to `mysite`::

    <distributionManagement>
        <repository>
            <id>mysite</id>
            <url>scpexe://mysite/var/www/mvn.0x0b.de/htdocs</url>
        </repository>
    </distributionManagement>

and finally execute::

    mvn deploy

to build the PenchY zip and upload it to your server.

Please keep in mind that if you change the repository from which
your clients will receive PenchY from, you also need to edit
:class:`~penchy.maven.BootstrapPOM` in :file:`penchy/maven.py` to
reflect this change.

If you remove ``repo`` from the ``DEPENDENCY`` dictionary completely,
your nodes need to know where to find PenchY by itself. This is
usually done by setting up a :file:`~/.m2/settings.xml` on the
nodes.

Updating PenchY
---------------
When you add features to PenchY such as new filters or workloads,
you will have to update PenchY in your maven repository.

This can be accomplished by increasing the version number in
:file:`mvn/penchy/pom.xml` and simply running::

    mvn deploy

The version number in PenchY's source code will automatically
replaced by the
`maven replacer plugin <http://code.google.com/p/maven-replacer-plugin/>`_.

Deploying Tamiflex via Maven
----------------------------
PenchY ships with a Project Object Model for
`Tamiflex <http://code.google.com/t/tamiflex/>`_, which is located
in :file:`mvn/poa/pom.xml`. If you wish to host Tamiflex
by yourself, you'll need to edit the Project Object Model and set
the server you wish to upload to. Afterwards, you can simply call::

    mvn deploy

Maven will then automatically download Tamiflex from its website
using the `wagon maven plugin <http://mojo.codehaus.org/wagon-maven-plugin/>`_.
and deploy it to your server.

Yet again, when using your own repository for tamiflex, you'll have
to change the location of :class:`~penchy.jobs.workloads.Dacapo` in
:file:`penchy/jobs/workloads.py`.

Declaring Maven Dependencies
----------------------------
PenchY is using Maven to handle dependencies which Workloads
might have.

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

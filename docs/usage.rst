=====
Usage
=====
This document explains the basic usage of PenchY.

There is only a single entry point to PenchY, the ``penchy`` command,
which takes quite a few command line parameters.

Command Line Parameters
-----------------------
The command line parameters of ``penchy`` explained:

 * ``-h`` or ``--help``
   shows a help message and exit
 * ``-c CONFIG`` or ``--config config`` specifies a configuration file. Please
   consult the :ref:`cfg` file section in order to learn how to
   write such a file. This argument defaults to ``~/.penchyrc``.
 * ``--logfile``
   specifies the file to which PenchY will log. Please note that PenchY will
   automatically rotate logfiles, so if you pass ``--logfile foo.log``,
   ``foo.log.1`` might be created by PenchY.
 * ``-d`` or ``--debug``
   sets the log level to ``DEBUG``.
 * ``-q`` or ``--quiet``
   sets the log level to ``WARNING``.
 * ``--check``
   checks a job for validity only.
 * ``--visualize``
   visualize the dependencies of the job's pipelines as Graph (needs Graphviz).
 * ``--run-locally``
   runs a job locally without the involvement of client/server
   communication. This requires the ``hostname`` passed to
   :class:`penchy.jobs.job.NodeSetting` to be ``localhost``.
 * ``-f`` or ``--load-from`` will load PenchY from the path supplied
   instead of acquiring it using maven. This is a pretty nifty feature
   if you are working on the client code and don't want to deploy
   the changes using maven as you write it. A simple scenario might
   be copying your PenchY version to the nodes using rsync and then
   using that version. Let's say you are using rsync to copy your
   version of PenchY to ``/tmp/penchy2``, then you'd need to pass
   ``-f /tmp/penchy2`` to the ``penchy`` command on the server, which
   will result in all nodes loading PenchY from this path.

.. _cfg:

Configuration File
------------------
PenchY provides a framework for using a configuration file. The configuration
file, by default located at ``~/.penchyrc``, is actually a Python file itself.
The following options are required in order to run PenchY:

* ``SERVER_HOST`` describes the hostname or IP address of the server penchy will be run on.
  This is not one of the nodes where the benchmark will be run, but the one deploying
  PenchY and collecting the resuts.
* ``SERVER_PORT`` describes the port on which penchy will listen on for incoming
  benchmark results.

In addition to the options above, you can define whatever options you like and
use them in your jobs. Just make sure to ``import config`` in your jobs and then
use ``config.MY_SETTING``.

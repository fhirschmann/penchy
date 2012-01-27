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
 *  ``-c CONFIG`` or ``--config config``
   specifies a configuration file. Please consult the :ref:`cfg` file
   section in order to learn how to write such a file.
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
 * ``--run-locally``
   runs a job locally without the involvement of client/server
   communication. This requires the ``hostname`` passed to
   :class:`penchy.jobs.job.NodeSetting` to be ``localhost``.

.. _cfg:

Configuration File
------------------


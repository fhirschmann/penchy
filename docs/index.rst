====================================================
PenchY -- JVM Provisioning & Reporting Documentation
====================================================

This is the documentation for PenchY, the Python Benchmarking Automation
Tool for Java Virtual Machines. 

PenchY is a tool which allows you to execute benchmarks for the
Java Virtual Machine on one or more hosts. It will take care of
the deployment of these jobs, install the required dependencies,
execute the job remotely, and send back the results to the server.
It does so in a very *flexible way*, and great care has been taken
in order to make PenchY *extensible*.

This is why the PenchY architecture makes heavy use of the
*flow-based programming paradigm*, where you can plug together
componentents of a so-called pipeline in a very intuitive
fashion. In the most simple scenario, you execute a benchmark
on a remote host, filter the output, and send it back to a server,
where it is plotted. These filters can not only be on the client,
but also on the server.

For a quick demonstration of what PenchY is capable of, skip
to the :doc:`examples`.

If you want to learn more, please follow these steps in order
to get your PenchY up and running:

.. toctree::
   :maxdepth: 2

   download
   installation
   configuration
   usage
   job
   extending
   examples
   maven
   examples
   arch
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


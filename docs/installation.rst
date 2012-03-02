============
Installation
============

This section will guide you through installing PenchY and its
dependencies.

Client-Side
-----------

Besides the python interpreter, PenchY has no python client-side dependencies
whatsoever. However, a valid maven installation is required, of course.

Server-Side
-----------

In addition to python itself, the following python packages are required:
 * paramiko
 * argparse
 * numpy
 * matplotlib

On debian, these packages can be installed with a single command::

    apt-get install python-paramiko python-argparse python-numpy python-matplotlib

Once you have downloaded PenchY, extract it to a folder of your choice and
continue with the :doc:`configuration`.

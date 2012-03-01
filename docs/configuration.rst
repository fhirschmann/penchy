Configuration
=============
PenchY provides a framework for using a configuration file. The configuration
file, by default located at ``~/.penchyrc``, is actually a Python file itself.
The following options are **required** in order to run PenchY:

* ``SERVER_HOST`` describes the hostname or IP address of the server penchy will be run on.
  This is not one of the nodes where the benchmark will be run, but the one deploying
  PenchY and collecting the resuts.
* ``SERVER_PORT`` describes the port on which penchy will listen on for incoming
  benchmark results.

The following options are **optional**:

* ``LOGFILE`` path of logfile to log to. The logfile will be rotated in each run.

In addition to the options above, you can define whatever options you like and
use them in your jobs. Just make sure to ``import config`` in your jobs and then
use ``config.MY_SETTING``.

Node Configuration
-------------------

It is recommended to put node definition in the configuration rather than
the job. A node setup could look like this::

    x86NODE = NodeSetting('192.168.56.10', SSH_PORT, USERNAME, '/home/bench', '/usr/bin')
    x64NODE = NodeSetting('192.168.56.11', SSH_PORT, USERNAME, '/home/bench', '/usr/bin')

Please consoult the :class:`~penchy.jobs.job.NodeSetting` documentation in order
to learn what arguments can be passed.

Public Key Authentication
-------------------------

The above will only work if you use passphraseless SSH public key authentication. If your
private key happens to have a passphrase and you are not running ssh-agent, you can
specify the passphrase like so::

    x86NODE = NodeSetting('192.168.56.10', SSH_PORT, USERNAME, '/home/bench', '/usr/bin',
                          keyfile='/home/me/.ssh/foo.x86', password='foo')
    x64NODE = NodeSetting('192.168.56.11', SSH_PORT, USERNAME, '/home/bench', '/usr/bin',
                          password='bar')

In the former case, the password ``foo`` is used to unlock the private key located in
``/home/me/.ssh/foo.x86`` and in the latter case, the password ``bar`` is used to unlock
the default private key.

Password Authentication
-----------------------

If you don't use public key authentication, you can use simple passwords as well::

    x86NODE = NodeSetting('192.168.56.10', SSH_PORT, USERNAME, '/home/bench', '/usr/bin',
                          password='foo')

In this case, the password ``foo`` is used to authenticate with this node. If you are
not willing to put your password into your configuration file, you can, of course, also
use ``getpass`` to enter the password on demand::

    from getpass import getpass
    x86NODE = NodeSetting('192.168.56.10', SSH_PORT, USERNAME, '/home/bench', '/usr/bin',
                          password=getpass())


"""
Library which abstracts SFTP and FTP connections

 .. moduleauthor:: Fabian Hirschmann <fabian@hirschm.net>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import logging
import shutil
from contextlib import contextmanager

from penchy import is_server

if is_server:
    import ftplib
    import paramiko


log = logging.getLogger(__name__)


class Deploy(object):
    """
    Base class from which all deployment methods must
    inherit from.
    """
    def __init__(self, hostname, username, password, port=None):
        """
        :param hostname: hostname of the host
        :type hostname: str
        :param username: username on the host
        :type username: str
        :param password: password on the host
        :type password: str
        :param port: port of the service
        :type port: int
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

    def connect(self):
        """
        Establish connection to this host.
        """
        raise NotImplementedError("connect must be implemented")

    def disconnect(self):
        """
        Disconnect from this host.
        """
        raise NotImplementedError("disconnect must be implemented")

    def put(self, local, remote):
        """
        Upload a file to this host.

        :param local: file to upload
        :type local: str
        :param remote: destination to upload to
        :type remote: str
        """
        raise NotImplementedError("put must be implemented")

    @property
    def connected(self):
        """
        Indicates if we are connected to the host.
        """
        raise NotImplementedError("connected must be implemented")

    @contextmanager
    def connection_required(self):
        """
        Contextmanager to make sure we are connected before
        uploading to this host.
        """
        if not self.connected:
            self.connect()

        yield

        if self.connected:
            self.disconnect()


class FTPDeploy(Deploy):
    """
    Provides communication with a FTP Server.
    """
    def __init__(self, *args, **kwargs):
        super(FTPDeploy, self).__init__(*args, **kwargs)

    def connect(self):
        self.conn = ftplib.FTP(self.hostname, self.username, self.password)

    def put(self, local, remote):
        with open(local, 'rb') as upload:
            self.conn.storbinary('STOR %s' % remote, upload)

    def disconnect(self):
        if self.conn:
            self.conn.quit()
        self.conn = None

    @property
    def connected(self):
        return self.conn is not None


class SFTPDeploy(Deploy):
    """
    Provides communication with a SFTP Server.

    If you require to set a different private key file, you can::

        d = SFTPDeploy('0x0b.de', 'foo', None)
        d.keyfile = '/home/foo/.ssh/id_rsa123

    """
    def __init__(self, *args, **kwargs):
        """
        :param hostname: hostname of the host
        :type hostname: str
        :param username: username on the host
        :type username: str
        :param keyfile: private key to use
        :type keyfile: str
        :param password: password on the host
                         can be empty for passphraseless
                         public key authentication or set
                         to the passphrase of a key
        :type password: str
        :param port: port of the service
        :type port: int
        """
        self.keyfile = kwargs.pop('keyfile') if 'keyfile' in kwargs else None
        super(SFTPDeploy, self).__init__(*args, **kwargs)
        self.ssh = None
        self.sftp = None

    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if not self.keyfile:
            self.ssh.load_system_host_keys()
        self.ssh.connect(self.hostname, username=self.username,
                port=self.port or 22, password=self.password,
                key_filename=self.keyfile)
        self.sftp = self.ssh.open_sftp()

    def put(self, local, remote):
        log.debug('Uploading %s to %s' % (local, remote))
        self.sftp.put(local, remote)

    def disconnect(self):
        self.sftp.close()
        self.ssh.close()

    @property
    def connected(self):
        if not self.ssh:
            return False

        transport = self.ssh.get_transport()
        if transport and transport.is_active():
            return True
        return False


class CopyDeploy(Deploy):
    """
    Allows you to copy files locally.
    """
    def __init__(self):
        super(SFTPDeploy, self).__init__(None, None, None)

    def connect(self):
        pass

    def dissconnect(self):
        pass

    def put(self, local, remote):
        shutil.copyfile(local, remote)

    def disconnect(self):
        pass

    @property
    def connected(self):
        return True

"""
Library which abstracts SFTP and FTP connections

 .. moduleauthor:: Fabian Hirschmann <fabian@hirschm.net>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import os
import logging
import shutil
from abc import ABCMeta, abstractmethod, abstractproperty
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
    __metaclass__ = ABCMeta

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

    @abstractmethod
    def connect(self):
        """
        Establish connection to this host.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Disconnect from this host.
        """
        pass

    @abstractmethod
    def put(self, local, remote):
        """
        Upload a file to this host.

        :param local: file to upload
        :type local: str
        :param remote: destination to upload to
        :type remote: str
        """
        pass

    @abstractproperty
    def connected(self):
        """
        Indicates if we are connected to the host.
        """
        pass

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
        """
        :param hostname: hostname of the host
        :type hostname: str
        :param username: username on the host
        :type username: str
        :param password: password on the host
        :type password: str
        :param port: port of the service
        :type port: int
        :param tls: use TLS support as described in RFC 4217 (defaults to True)
        :type tls: boolean
        :param passive: ftp passive mode (defaults to True)
        :type passive: boolean
        """
        tls = kwargs.pop('tls') if 'tls' in kwargs else False
        passive = kwargs.pop('passive') if 'passive' in kwargs else True
        super(FTPDeploy, self).__init__(*args, **kwargs)

        self.conn = ftplib.FTP_TLS() if tls else ftplib.FTP()
        self.conn.set_pasv(passive)
        self._connected = False

    def connect(self):
        self.conn.connect(self.hostname, self.port or 21)
        self.conn.login(self.username, self.password)
        self._connected = True

    def put(self, local, remote):
        self.conn.cwd(os.path.dirname(remote))
        with open(local, 'rb') as upload:
            self.conn.storbinary('STOR %s' % os.path.basename(remote), upload)

    def disconnect(self):
        if self.conn:
            self.conn.quit()
        self._connected = False

    @property
    def connected(self):
        return self._connected


class SFTPDeploy(Deploy):
    """
    Provides communication with a SFTP Server.
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
        super(CopyDeploy, self).__init__(None, None, None)

    def connect(self):
        pass

    def disconnect(self):
        pass

    def put(self, local, remote):
        shutil.copyfile(local, remote)

    @property
    def connected(self):
        return True

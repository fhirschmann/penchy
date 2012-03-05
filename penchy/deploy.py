from contextlib import contextmanager

from penchy import is_server

if is_server:
    import ftplib
    import paramiko


class Deploy(object):
    def __init__(self, hostname, username, password, port=None):
        """
        :param hostname: hostname of the host
        :type hostname: str
        :param username: username on the host
        :type username: str
        :param password: password on the host
        :type password: str
        :param path: path to upload to
        :type path: str
        :param port: port of the service
        :type port: int
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

    def connect(self):
        raise NotImplementedError("connect must be implemented")

    def disconnect(self):
        raise NotImplementedError("disconnect must be implemented")

    def put(self, local):
        raise NotImplementedError("put must be implemented")

    @property
    def connected(self):
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
    def __init__(self, *args, **kwargs):
        super(SFTPDeploy, self).__init__(*args, **kwargs)
        self.ssh = None
        self.sftp = None

    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.load_system_host_keys()
        self.ssh.connect(self.hostname, username=self.username,
                port=self.port or 22, password=self.password)
        self.sftp = self.ssh.open_sftp()

    def put(self, local, remote):
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


if __name__ == '__main__':
    import paramiko
    s = SFTPDeploy('localhost', 'fabian', None)
    with s.connection_required():
        s.put('test.txt', '/tmp/foo.xx')

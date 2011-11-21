#!/usr/bin/env python

import os
import sys
import paramiko
import logging

from config import *

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("server")

if __name__ == "__main__":
    for node in NODES:
        log.info("Connecting to Node %s" % str(node))
        transport = paramiko.Transport((node[0], node[1]))
        transport.connect(username=node[2],
                pkey = paramiko.RSAKey.from_private_key_file(ID_RSA))
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        try:
            sftp.mkdir(node[3])
        except IOError:
            log.debug("Directory %s exists already" % node[3])

        for f in FILES:
            rloc = node[3] + os.path.sep + os.path.basename(f)
            log.info("Copying file %s to %s" % (f, rloc))
            sftp.put(sys.path[0] + '/' + f, rloc)

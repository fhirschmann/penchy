"""
This module provides the foundation on which the
PenchY job description language is build upon.
"""
from penchy.jobs import jvms, tools, filters, workloads
from penchy.jobs.job import Job, SystemComposition, NodeSetting
from penchy.util import Value, extract_maven_credentials
from penchy.deploy import SFTPDeploy, FTPDeploy

JVM = jvms.JVM

# all job elements that are interesting for the user have to be enumerated here
__all__ = [
    # job
    'Job',
    'NodeSetting',
    'SystemComposition',
    'Value',
    'SFTPDeploy',
    'FTPDeploy',
    'extract_maven_credentials',
    # jvms
    'JVM',
    # modules
    'filters',
    'jvms',
    'hooks',
    'plots',
    'workloads',
    'tools',
]

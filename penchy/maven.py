#!/usr/bin/env python

class MavenDependency(object):
    """
    This class represents a dependency which can be found in a 
    maven repository.

    A sample dependency might look like::

        MavenDependency("de.tu_darmstadt.penchy", "poa", "2.0.0.0", "http://mvn.0x0b.de")
    """
    def __init__(self, groupid, artifact, version, repo=None):
        """
        :param groupid: the groupId
        :type groupid: string
        :param artifact: the artifact
        :type artifact: string
        :param version: the version
        :type version: string
        :param repo: the repository to load from
        :type repo: string
        """

        self.groupid = groupid
        self.artifact = artifact
        self.version = version
        self.repo = repo

    def __eq__(self, other):
        return self.get_cmd() == other.get_cmd()

    def get_cmd(self):
        """
        Build the command line which installs this dependency.

        :return: maven call with arguments
        :rtype: list
        """

        cmd = ['mvn', 'dependency:get']

        if self.repo:
            cmd.append('-DrepoUrl=' + self.repo)
        else:
            cmd.append('-DrepoUrl=' + 'http://repo1.maven.org/maven2')


        cmd.append('-Dartifact=%s:%s:%s' % (self.groupid, 
            self.artifact, self.version))

        return cmd


if __name__ == "__main__": 
    x = MavenDependency('de.tu_darmstadt.penchy', 'booster', '2.0.0.0', 'http://mvn.0x0b.de')
    print x.get_maven_cmd()

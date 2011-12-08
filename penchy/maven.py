#!/usr/bin/env python

class MavenDependency(object):
    """
    This class represents a dependency which can be found in a 
    maven repository.
    """
    def __init__(self, groupid, artifact, version, repo=None):
        """
        :param groupid: the groupId
        :type groupid: string
        :param artifact: the artifact
        :type artifact: string
        :param version: the version
        :type version: string
        """

        self.groupid = groupid
        self.artifact = artifact
        self.version = version
        self.repo = repo

    def __eq__(self, other):
        return self.get_maven_cmd() == other.get_maven_cmd()

    def get_maven_cmd(self):
        """
        Build the command line which installs this dependency.

        :return: maven call with arguments
        """

        cmd = ['mvn', 'dependency:get']

        if self.repo:
            cmd.append('-DrepoUrl=' + self.repo)
        else:
            cmd.append('-DrepoUrl=' + 'http://repo1.maven.org/maven2')


        cmd.append('-Dartifact=%s:%s:%s' % (self.groupid, 
            self.artifact, self.version))

        return " ".join(cmd)


if __name__ == "__main__": 
    x = MavenDependency('de.tu_darmstadt.penchy', 'booster', '2.0.0.0', 'http://mvn.0x0b.de')
    print x.get_maven_cmd()

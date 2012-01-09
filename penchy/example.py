#!/usr/bin/env python

from penchy.maven import BootstrapPOM, POM, MavenDependency, get_classpath
from penchy.jobs.workloads import ScalaBench

if __name__ == "__main__":
    b = BootstrapPOM()
    for d in ScalaBench.DEPENDENCIES:
        b.add_dependency(d)
    b.write('pom.xml')
    print get_classpath()

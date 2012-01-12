Maven Documentation
===================
This document describes how PenchY makes use of Maven.

Project Object Models
---------------------
PenchY incorporates several Project Object Models (POMs) in
order to deploy all the dependencies required by PenchY as
well as PenchY itself.

The POM structure looks as follows::

    mvn/pom.xml (1)
    mvn/pia/pom.xml (2)
    mvn/poa/pom.xml (3)
    mvn/booster/pom.xml (4)
    mvn/asm/pom.xml (5)
    pom.xml (6)

where the individual POMs can be described as

#. The **Parent** Model. This is responsible for defining the 
   output repository.
#. The **PIA** Model. This will package PIA, which is part of Tamiflex [#f1]_.
#. The **POA** Model. Similar to (3).
#. The **Booster** Model. Similar to (3).
#. The **ASM** Model. This packages [#f2]_.
#. The **PenchY** Model. This model generates a zip of the Python code.

Deploying the 3rd Party Dependencies
------------------------------------
You can deploy the 3rd party dependencies, such as tamiflex, by
issuing::

    make deploy-all

which will deploy Tamiflex and PenchY to the repository specified in 
the parent POM (1).

Declaring Maven Dependencies
----------------------------
Maven dependencies can be declared using the `MavenDependeny` module:

.. autoclass:: penchy.maven.MavenDependency

Once the dependencies have been declared, they will be collected and
installed on the nodes via maven pom files.


.. [#f1] Tamiflex: http://code.google.com/p/tamiflex/
.. [#f2] ASM: http://asm.ow2.org/

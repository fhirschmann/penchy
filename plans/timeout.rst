=============
 Timeout Test
=============

Vorbedingungen
==============

Virtuelle Maschinen mit den IP-Adressen

- 192.168.56.11

stehen bereit, auf ihnen ist Maven und Python(2.6) installiert.
PenchY wird mit dem ``-d`` (debug) Parameter gestartet.

Job
===

/examples/timeout.job

Während der Ausführung
======================

Die Logs des Servers werden protokolliert. Nach etwa fünf
Sekunden wird sich PenchY automatisch beenden.

Nachbedingungen
===============

In den Logdateien des Servers und des Clients muss erkennbar
sein, dass ein Timeout eingetreten ist. Die JVM muss mit einer
Exception abgebrochen worden sein. Auf den Nodes dürfen keine
JVM Prozesse mehr laufen.

=====================
 Vorzeitiger Abbruch
=====================

Vorbedingungen
==============

Virtuelle Maschinen mit den IP-Adressen

- 192.168.56.11
- 192.168.56.10

stehen bereit, auf ihnen ist Maven und Python(2.6) installiert.

Job
===

/plans/jobs/2nodes_infinite.job

Während der Ausführung
======================

Die Nodes werden mittels des ``top`` Kommandos überwacht. Alsbald
der erste Java Prozess zu sehen ist, wird der Job am Server durch ein
Keyboard Interrupt abgebrochen.

Nachbedingungen
===============

Auf den Nodes darf kein JVM oder Maven Prozess mehr laufen.

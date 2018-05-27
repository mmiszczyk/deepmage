Deepmage
=========

Introudction
------------

Deepmage is a terminal-based hex editor for non-octet-oriented
data. Its goal is to easily allow you to operate at the level of
individual bits and n-bit words. This is the functionality I
missed in most of the free hex editors, which were obviously made
with 8-bit bytes in mind. Of course 8-bit bytes are good enough
for most users, but people who do a lot of security research
and/or reversing might know of a few frustrating situations in
which the assumption that everything divides neatly into octets
was proven false. For me, it was first with baseband (7-bit
packed GSM alphabet) and with codecs (variable-length bitfields).

Status
------

Deepmage is at the very early stage of development. So far, it
can read files (while only keeping what's needed in memory),
interpret their contents at different word sizes and display
them either as hex digits or bits. Most of the options aren't
yet exposed in the user interface and have to be accessed by
modifying the code. The code also lacks comments and
documentation. All of those things are, of course, coming soon -
so stay patient.
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

Deepmage is currently in the alpha version. The code needs some
refactoring, there's not real documentation and few comments
and it works really slow if your terminal windows is big - but
the basic functionality is there.

Deepmage allows you to view and edit files like in a normal hex
editor, but you can also directly edit bits or change word (note
that 'word' here means a basic unit, not machine word) size to
something different than the usual 8 bits. It supports large file
by only keeping in memory the parts of the file that have unsaved
changes or are currently displayed to the user.

Dependencies
------------
+ asciimatics
+ bitstring
+ hy

How to use
----------
You can download this repo
```bash
git clone https://github.com/mmiszczyk/deepmage
```

or get deepmage from PyPi

```bash
pip3 install deepmage
```

Then, to use the editor:

```bash
./deepmage [PATH_TO_FILE]
```

Use arrow keys, page up/page down and home/end to navigate.

Switch between hex and bit modes with F2.

Save changes with F5.

Exit with F10 or CTRL+C.

Usage for dumping/parsing scripts:

```bash
usage: deepmage-hexdump [-h] [-w wordsize] [-c cols] [-b] file

positional arguments:
  file                  Path to a file to edit

optional arguments:
  -h, --help            show this help message and exit
  -w wordsize, --wordsize wordsize
                        Size of words (in bits)
  -c cols, --cols cols
  -b, --bits
```

```bash
usage: deepmage-hexdump [-h] [-w wordsize] [--write_buffer_size bytes] [-b]
                        [-i]
                        [input-filename] output-filename

positional arguments:
  input-filename        Path to a hexdump file
  output-filename       Path to an output file

optional arguments:
  -h, --help            show this help message and exit
  -w wordsize, --wordsize wordsize
                        Size of words (in bits)
  --write_buffer_size bytes
  -b, --bits
  -i, --ignore-errors   Skip invalid characters
  ```

TODO
----

### Planned
+ tools for dumping and parsing bitstreams (for use with Unix shell
scripts)
+ fixing any bugs that will come out during testing

### Maybe
+ performance improvements
+ UI code refactoring
+ two-column display with approximate ASCII representation

### Long-term (unlikely)
+ parsing user-defined structure with words of different length,
including variable-length bitfields
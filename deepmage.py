from time import sleep
from asciimatics.screen import Screen

import hy
import bitstream_reader

# TODO: open file provided by user
with open('a.bin', 'r+b') as f:
    x = bitstream_reader.FileReader(f, 1024)

    # TODO: actual hex editor
    def demo(screen):
        x[0] = [False, True, False, False, False, False, True, False]
        screen.print_at(str(x[0]), 0, 0)
        x.save()
        screen.refresh()
        sleep(1)


    Screen.wrapper(demo)

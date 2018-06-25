#######################
# This file is a part #
#   of the deepmage   #
#  project, released  #
# under the GNU GPL 3 #
#      license        #
#  (see the COPYING   #
#  file for details)  #
#######################

import math
import os
import errno

# noinspection PyUnresolvedReferences
import hy  # warning suppressed because that import is needed to run hy code if it's not compiled to .pyc yet
import bitstring
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent

from libdeepmage import bitstream_reader
from libdeepmage import cursor

BIT_MODE = 1
HEX_MODE = 4

UNSAVED_CHANGES = "[MODIFIED]"
WORDSIZE_PROMPT = "New wordsize (in bits): "
WORDSIZE_HELP   = "<ENTER> confirm | <ESC> cancel"
KEYS_HELP       = "<F2> Bit/Hex mode | <F3> Change wordsize | <F5> Save | <F10> Exit"

loop = None


class UI(object):

    UI_control_keys = {Screen.KEY_F2:  lambda self: self.mode_toggle(),
                       Screen.KEY_F3:  lambda self: self.change_wordsize(),
                       Screen.KEY_F5:  lambda self: self.reader.save(),
                       Screen.KEY_F10: lambda self: exit(0)}

    hex_alphabet = {ord(x) for x in '0123456789abcdefABCDEF'}
    bin_alphabet = {ord(x) for x in '01'}

    def __init__(self, screen, file):
        self.screen = screen
        self.file = file
        self.reader = bitstream_reader.FileReader(self.file, 1024)
        self.reader.set_wordsize(8)
        self.mode = HEX_MODE
        self.representation = hex_representation
        self.cursor = cursor.BasicCursor(self)
        self.starting_word = 0
        self.chars_per_word = int(math.ceil(self.reader.get_wordsize() / self.mode))
        self.words_in_line = self.calculate_words_in_line()
        self.lines = self.screen.height - 3  # 1 line for header and 2 for footer
        self.total_words = self.reader.get_wordcount()
        self.words_in_view = self.lines * self.words_in_line
        self.view = None
        self.view_changed = True
        self.screen.print_at(self.make_header_text(self.file.name),
                             0, 0,
                             Screen.COLOUR_CYAN,
                             Screen.A_BOLD and Screen.A_REVERSE)
        self.screen.print_at(self.make_header_text(KEYS_HELP),
                             0, self.screen.height - 1,
                             Screen.COLOUR_CYAN,
                             Screen.A_REVERSE)
        self.main_loop_internal()

    def draw_view(self):
        self.view = self.reader.get_view(self.starting_word, self.words_in_view)
        for line_number in range(self.lines):
            pos = 0
            for word_number in range(self.words_in_line):
                current_word = line_number * self.words_in_line + word_number
                if current_word + self.starting_word >= self.total_words:
                    self.screen.print_at((' ' * self.chars_per_word), pos, line_number + 1)
                else:
                    self.screen.print_at(self.representation(self.view[current_word]),
                                         pos, line_number + 1)
                pos += self.chars_per_word
                self.screen.print_at(' ', pos, line_number + 1)
                pos += 1
                if pos < self.screen.width - 1:
                    self.screen.print_at(' ' * (self.screen.width - pos - 1), pos, line_number + 1)
        self.view_changed = False
        self.cursor.old_coords = self.cursor.coords

    def calculate_words_in_line(self):
        return max(1, self.screen.width //
                   (self.chars_per_word + 1))  # 1 char for a separator

    def make_header_text(self, text):
        if len(text) == self.screen.width:
            return text
        if len(text) > self.screen.width:
            return text[:self.screen.width - 3] + '...'
        pad = ' ' * ((self.screen.width - len(text)) // 2)
        return pad + text + pad

    def handle_cursor_move(self):
        self.screen.print_at(self.cursor.get_human_readable_position_data(), 0, self.screen.height - 2)
        self.cursor.highlight()

    def handle_screen_resize(self):
        self.chars_per_word = int(math.ceil(self.reader.get_wordsize() / self.mode))
        self.words_in_line = self.calculate_words_in_line()
        self.lines = self.screen.height - 2  # 1 line for header and 1 for footer
        self.words_in_view = self.lines * self.words_in_line
        self.screen = Screen.wrapper(loop)
        self.screen.clear()

    def redraw_if_needed(self):
        needs_refresh = False
        if self.screen.has_resized():
            self.handle_screen_resize()
            needs_refresh = True
        if self.view_changed:
            self.draw_view()
            needs_refresh = True
        if self.cursor.old_coords is not None:
            self.handle_cursor_move()
            needs_refresh = True
        if len([x for x in self.reader.chunks if x.modified]):
            self.screen.print_at(UNSAVED_CHANGES, self.screen.width - len(UNSAVED_CHANGES), self.screen.height-2)
        if needs_refresh:
            self.screen.refresh()

    def handle_keyboard_events(self, k):
        try:
            self.cursor.write_at_cursor(k)
            return
        except ValueError:
            pass
        try:
            self.UI_control_keys[k](self)
            return
        except KeyError:
            pass
        self.cursor.handle_key_event(k)

    def main_loop_internal(self):
        while True:
            e = self.screen.get_event()
            if type(e) == KeyboardEvent:
                self.handle_keyboard_events(e.key_code)
            self.redraw_if_needed()

    def mode_toggle(self):
        curr_word = self.cursor.word_idx_in_file()
        self.view_changed = True
        self.mode = BIT_MODE if self.mode == HEX_MODE else HEX_MODE
        cursor_type = cursor.BitCursor if self.mode == BIT_MODE else cursor.BasicCursor
        self.representation = bit_representation if self.mode == BIT_MODE else hex_representation
        self.chars_per_word = int(math.ceil(self.reader.get_wordsize() / self.mode))
        self.words_in_line = self.calculate_words_in_line()
        self.cursor.coords = (curr_word % self.words_in_line,
                              (curr_word // self.words_in_line) % self.lines)
        self.words_in_view = self.lines * self.words_in_line
        self.starting_word = curr_word - (curr_word % self.words_in_view)
        self.cursor = cursor_type(self, self.cursor.coords)

    def change_wordsize(self):
        self.screen.print_at(WORDSIZE_PROMPT, 0, self.screen.height - 2)
        self.screen.print_at(WORDSIZE_HELP, self.screen.width - len(WORDSIZE_HELP), self.screen.height - 2)
        self.screen.refresh()
        buffer = []
        while True:
            e = self.screen.get_event()
            if e is None or type(e) != KeyboardEvent:
                continue
            try:
                c = chr(e.key_code)
                if c in [x for x in '1234567890']:
                    buffer.append(c)
                if c in [x for x in '\r\n']:
                    self.reader.set_wordsize(int(''.join(buffer)))
                    self.chars_per_word = int(math.ceil(self.reader.get_wordsize() / self.mode))
                    self.words_in_line = self.calculate_words_in_line()
                    self.total_words = self.reader.get_wordcount()
                    self.words_in_view = self.lines * self.words_in_line
                    self.view_changed = True
                    break
            except ValueError:
                k = e.key_code
                if k == Screen.KEY_BACK or k == Screen.KEY_DELETE or k == Screen.KEY_LEFT:
                    self.screen.print_at(' ', len(WORDSIZE_PROMPT) + len(buffer) - 1, self.screen.height - 2)
                    buffer = buffer[:-1]
                elif k == Screen.KEY_ESCAPE:
                    self.screen.print_at(' ' * self.screen.width, 0, self.screen.height-2)
                    self.screen.refresh()
                    break
            self.screen.print_at(buffer, len(WORDSIZE_PROMPT), self.screen.height-2)
            self.screen.refresh()


def hex_representation(word):
    if word is None or len(word) == 0:
        return ''
    if not len(word) % 4:
        ret = word
    else:
        split = [word[i:i + 4] for i in range(0, len(word), 4)]
        split[-1] = ([False] * (4 - len(split[-1]))) + split[-1]
        ret = [bit for hex_digit in split for bit in hex_digit]
    return bitstring.BitString(ret).hex


def bit_representation(word):
    return bitstring.BitString(word).bin


def main(filename):
    global loop
    try:
        if os.stat(filename).st_size == 0:
            raise EOFError
    except FileNotFoundError:
        print("{}: no such file or directory".format(filename))
        exit(errno.ENOENT)
    except EOFError:
        print("{}: file is empty".format(filename))
        exit(errno.ENODATA)

    with open(filename, 'r+b') as f:

        def main_loop(screen):
            UI(screen, f)

        loop = main_loop
        try:
            Screen.wrapper(loop)
        except KeyboardInterrupt:
            exit(0)

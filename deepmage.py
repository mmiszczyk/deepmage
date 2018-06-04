import math
import bitstring
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent

import hy
import bitstream_reader
import cursor

BIT_MODE = 1
HEX_MODE = 4


class UI(object):

    UI_control_keys = {Screen.KEY_F2:  lambda self: self.mode_toggle(),
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
        self.chars_per_word = int(math.ceil(reader.get_wordsize() / self.mode))
        self.words_in_line = self.calculate_words_in_line()
        self.lines = self.screen.height - 2  # 1 line for header and 1 for footer
        self.total_words = reader.get_wordcount()
        self.words_in_view = self.lines * self.words_in_line
        self.view = None
        self.view_changed = True
        self.write_buffer = []
        self.screen.print_at(self.make_header_text(),
                             0, 0,
                             Screen.COLOUR_CYAN,
                             Screen.A_BOLD and Screen.A_REVERSE)
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
        self.view_changed = False
        self.cursor.old_coords = self.cursor.coords

    def calculate_words_in_line(self):
        return max(1, self.screen.width //
                   (self.chars_per_word + 1))  # 1 char for a separator

    def make_header_text(self):
        if len(self.file.name) == self.screen.width:
            return self.file.name
        if len(self.file.name) > self.screen.width:
            return self.file.name[:self.screen.width - 3] + '...'
        pad = ' ' * ((self.screen.width - len(self.file.name)) // 2)
        return pad + self.file.name + pad

    def handle_cursor_move(self):
        self.screen.print_at(('{}/{} {}' + ' ' * self.screen.width).format(
            self.cursor.word_idx_in_file() + 1, self.total_words, self.cursor.coords), 0, self.screen.height - 1)
        try:
            self.screen.print_at(self.representation(self.view[self.cursor.old_word_idx_in_view()]),
                                 self.cursor.old_coords[0] * (self.chars_per_word + 1), self.cursor.old_coords[1] + 1,
                                 attr=Screen.A_NORMAL)
            self.screen.print_at(self.representation(self.view[self.cursor.word_idx_in_view()]),
                                 self.cursor.coords[0] * (self.chars_per_word + 1), self.cursor.coords[1] + 1,
                                 attr=Screen.A_REVERSE)
        except IndexError:
            pass
        self.cursor.old_coords = None

    def handle_screen_resize(self):
        self.chars_per_word = int(math.ceil(self.reader.get_wordsize() / self.mode))
        self.words_in_line = self.calculate_words_in_line()
        self.lines = self.screen.height - 2  # 1 line for header and 1 for footer
        self.words_in_view = self.lines * self.words_in_line
        self.screen = Screen.wrapper(main_loop)
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
        if needs_refresh:
            self.screen.refresh()

    def handle_keyboard_events(self, k):
        if k in self.hex_alphabet and self.mode == HEX_MODE:
            self.write_buffer.append(k)
            if len(self.write_buffer) == self.chars_per_word:
                bits_to_write = bitstring.ConstBitArray('0x'+''.join([chr(x) for x in self.write_buffer]))
                self.reader[self.cursor.word_idx_in_file()] = bits_to_write[::-1][:self.reader.get_wordsize()][::-1]
                self.write_buffer = []
                self.view_changed = True
                k = Screen.KEY_RIGHT
            else:
                return
        try:
            self.UI_control_keys[k](self)
            return
        except KeyError:
            pass
        self.cursor.handle_key_event(k)
        self.write_buffer = []

    def main_loop_internal(self):
        while True:
            self.redraw_if_needed()
            e = self.screen.get_event()
            if type(e) == KeyboardEvent:
                self.handle_keyboard_events(e.key_code)

    def mode_toggle(self):
        curr_word = self.cursor.word_idx_in_file()
        self.view_changed = True
        self.mode = BIT_MODE if self.mode == HEX_MODE else HEX_MODE
        self.representation = bit_representation if self.mode == BIT_MODE else hex_representation
        self.chars_per_word = int(math.ceil(self.reader.get_wordsize() / self.mode))
        self.words_in_line = self.calculate_words_in_line()
        self.cursor.coords = (curr_word % self.words_in_line,
                              (curr_word // self.words_in_line) % self.lines)
        self.words_in_view = self.lines * self.words_in_line
        self.starting_word = curr_word - (curr_word % self.words_in_view)


def hex_representation(word):
    if word is None or len(word) == 0:
        return []
    if not len(word) % 4:
        ret = word
    else:
        split = [word[i:i + 4] for i in range(0, len(word), 4)]
        split[-1] = ([False] * (4 - len(split[-1]))) + split[-1]
        ret = [bit for hex_digit in split for bit in hex_digit]
    ret = bitstring.BitString(ret).hex
    return ret if len(ret) == 2 else '0' + ret


def bit_representation(word):
    return bitstring.BitString(word).bin


# TODO: open file provided by user
with open('a.bin', 'r+b') as f:
    reader = bitstream_reader.FileReader(f, 1024)

    # TODO: keyboard shortcuts for changing word size
    def main_loop(screen):
        UI(screen, f)


    Screen.wrapper(main_loop, catch_interrupt=True)

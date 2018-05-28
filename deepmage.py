import math
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent

import hy
import bitstream_reader
import bitstring

BIT_MODE = 1
HEX_MODE = 4


class UI(object):
    def __init__(self, screen, file):
        self.screen = screen
        self.file = file
        self.reader = bitstream_reader.FileReader(self.file, 1024)
        reader.set_wordsize(8)
        self.mode = HEX_MODE
        self.representation = hex_representation
        self.cursor = (0, 0)
        self.old_cursor = self.cursor
        self.cursor_at_word = 0
        self.starting_word = 0
        self.chars_per_word = math.ceil(reader.get_wordsize() / self.mode)
        self.words_in_line = self.calculate_words_in_line()
        self.lines = self.screen.height - 2  # 1 line for header and 1 for footer
        self.total_words = reader.get_wordcount()
        self.words_in_view = self.lines * self.words_in_line
        self.view = reader.get_view(self.starting_word, self.words_in_view)
        self.view_changed = True
        self.screen.print_at(self.make_header_text(),
                             0, 0,
                             Screen.COLOUR_CYAN,
                             Screen.A_BOLD and Screen.A_REVERSE)
        self.main_loop_internal()

    def draw_view(self):
        self.view = reader.get_view(self.starting_word, self.words_in_view)
        for line_number in range(self.lines):
            pos = 0
            for word_number in range(self.words_in_line):
                current_word = line_number * self.words_in_line + word_number
                if current_word + self.starting_word >= self.total_words:
                    self.screen.print_at((' ' * self.mode), pos, line_number + 1)
                else:
                    self.screen.print_at(self.representation(self.view[current_word]),
                                         pos, line_number + 1)
                pos += self.chars_per_word
                self.screen.print_at(' ', pos, line_number + 1)
                pos += 1
        self.view_changed = False
        self.old_cursor = self.cursor

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
        self.cursor_at_word = self.starting_word + (self.cursor[1] * self.words_in_line) + self.cursor[0]
        self.screen.print_at(('{}/{}' + ' ' * self.screen.width).format(
            self.cursor_at_word + 1, self.total_words), 0, self.screen.height - 1)
        self.screen.print_at(self.representation(self.view[self.old_cursor[1] * self.words_in_line +
                                                           self.old_cursor[0]]),
                             self.old_cursor[0] * (self.chars_per_word + 1), self.old_cursor[1] + 1,
                             attr=Screen.A_NORMAL)
        self.screen.print_at(self.representation(self.view[self.cursor[1] * self.words_in_line + self.cursor[0]]),
                             self.cursor[0] * (self.chars_per_word + 1), self.cursor[1] + 1,
                             attr=Screen.A_REVERSE)
        self.old_cursor = None

    def handle_screen_resize(self):
        self.chars_per_word = math.ceil(reader.get_wordsize() / self.mode)
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
        if self.old_cursor is not None:
            try:
                self.handle_cursor_move()
            except IndexError:
                pass
            needs_refresh = True
        if needs_refresh:
            self.screen.refresh()

    def handle_keyboard_events(self, k):
        old_start = self.starting_word
        if (k == Screen.KEY_RIGHT) and self.cursor_at_word < self.total_words - 1:
            self.old_cursor = self.cursor
            self.cursor = self.cursor[0] + 1, self.cursor[1]
        elif (k == Screen.KEY_LEFT) and self.cursor_at_word > 0:
            self.old_cursor = self.cursor
            self.cursor = self.cursor[0] - 1, self.cursor[1]
        elif (k == Screen.KEY_DOWN) and self.cursor_at_word < self.total_words - self.words_in_line:
            self.old_cursor = self.cursor
            self.cursor = self.cursor[0], self.cursor[1] + 1
        elif (k == Screen.KEY_UP) and self.cursor_at_word > self.words_in_line - 1:
            self.old_cursor = self.cursor
            self.cursor = self.cursor[0], self.cursor[1] - 1
        if self.cursor[0] >= self.words_in_line:
            self.cursor = 0, self.cursor[1] + 1
        if self.cursor[0] < 0:
            self.cursor = self.words_in_line - 1, self.cursor[1] - 1
        if self.cursor[1] < 0:
            self.starting_word = self.starting_word - self.words_in_line if self.starting_word > 0 else 0
            self.cursor = self.cursor[0], 0
        if self.cursor[1] >= self.lines:
            self.starting_word = self.starting_word + self.words_in_line
            self.cursor = self.cursor[0], self.lines - 1
        self.starting_word = min(self.starting_word, self.total_words - self.words_in_view +
                                 (self.starting_word % self.words_in_view))
        self.starting_word = max(self.starting_word, 0)
        if old_start != self.starting_word:
            self.view_changed = True

    def main_loop_internal(self):
        while True:
            self.redraw_if_needed()
            e = self.screen.get_event()
            if type(e) == KeyboardEvent:
                self.handle_keyboard_events(e.key_code)


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

    # TODO: modifying file contents
    # TODO: keyboard shortcuts for switching hex/bin mode, changing word size, saving, quitting
    # TODO: catch KeyboardInterrupt
    def main_loop(screen):
        UI(screen, f)


    Screen.wrapper(main_loop)

import math
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent

import hy
import bitstream_reader
import bitstring

BIT_MODE = 1
HEX_MODE = 4


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


def calculate_words_in_line(chars_per_word, screen_width):
    return max(1, screen_width //
               (chars_per_word + 1))  # 1 char for a separator


def make_header_text(text, width):
    if len(text) == width:
        return text
    if len(text) > width:
        return text[:width - 3] + '...'
    pad = ' ' * ((width - len(text)) // 2)
    return pad + text + pad


# TODO: open file provided by user
with open('a.bin', 'r+b') as f:
    reader = bitstream_reader.FileReader(f, 1024)

    # TODO: actual hex editor
    def main_loop(screen):
        mode = HEX_MODE
        cursor = (0, 0)
        starting_word = 0
        reader.set_wordsize(8)
        while True:
            chars_per_word = math.ceil(reader.get_wordsize() / mode)
            words_in_line = calculate_words_in_line(chars_per_word,
                                                    screen.width)
            lines = screen.height - 2  # 1 line for header and 1 for footer
            total_words = reader.get_wordcount()
            words_in_view = lines * words_in_line
            starting_word = min(starting_word, total_words - words_in_view + (starting_word % words_in_view))
            starting_word = max(starting_word, 0)
            print(starting_word)
            view = reader.get_view(starting_word, words_in_view)
            representation = bit_representation if mode == BIT_MODE else hex_representation

            screen.print_at(make_header_text(f.name, screen.width),
                            0, 0,
                            Screen.COLOUR_CYAN,
                            Screen.A_BOLD and Screen.A_REVERSE)
            cursor_at_word = starting_word + (cursor[1] * words_in_line) + cursor[0]
            screen.print_at(('{}/{}' + ' ' * screen.width).format(
                cursor_at_word + 1, total_words), 0, screen.height - 1)

            for line_number in range(lines):
                pos = 0
                for word_number in range(words_in_line):
                    current_word = line_number * words_in_line + word_number
                    if current_word + starting_word >= total_words:
                        screen.print_at((' ' * mode), pos, line_number + 1)
                        pass
                    else:
                        screen.print_at(representation(view[current_word]),
                                        pos, line_number + 1,
                                        attr=Screen.A_REVERSE if (word_number == cursor[0] and line_number == cursor[1])
                                        else Screen.A_NORMAL)
                    pos += chars_per_word
                    screen.print_at(' ', pos, line_number + 1)
                    pos += 1

            while True:
                if screen.has_resized():
                    screen = Screen.wrapper(main_loop)
                    screen.clear()
                screen.refresh()
                e = screen.get_event()
                if e is None or type(e) != KeyboardEvent:
                    continue
                k = e.key_code
                if (k == Screen.KEY_RIGHT) and cursor_at_word < total_words - 1:
                    cursor = cursor[0] + 1, cursor[1]
                elif (k == Screen.KEY_LEFT) and cursor_at_word > 0:
                    cursor = cursor[0] - 1, cursor[1]
                elif (k == Screen.KEY_DOWN) and cursor_at_word < total_words - words_in_line:
                    cursor = cursor[0], cursor[1] + 1
                elif (k == Screen.KEY_UP) and cursor_at_word > words_in_line - 1:
                    cursor = cursor[0], cursor[1] - 1
                if cursor[0] >= words_in_line:
                    cursor = 0, cursor[1] + 1
                if cursor[0] < 0:
                    cursor = words_in_line - 1, cursor[1] - 1
                if cursor[1] < 0:
                    starting_word = starting_word - words_in_line if starting_word > 0 else 0
                    cursor = cursor[0], 0
                if cursor[1] >= lines:
                    starting_word = starting_word + words_in_line
                    cursor = cursor[0], lines - 1
                break


    Screen.wrapper(main_loop)

from asciimatics.screen import Screen

import hy
import bitstream_reader
import bitstring

BIT_MODE = 1
HEX_MODE = 4


def hex_representation(word):
    if not len(word) % 4:
        ret = word
    else:
        split = [word[i:i+4] for i in range(0, len(word), 4)]
        split[-1] = ([False] * (4-len(split[-1]))) + split[-1]
        ret = [bit for hex_digit in split for bit in hex_digit]
    return bitstring.BitString(ret).hex


def bit_representation(word):
    return bitstring.BitString(word).bin


def calculate_words_in_line(chars_per_word, screen_width):
    return max(1, screen_width //
               (chars_per_word + 1))  # 1 char for a separator


def make_header_text(text, width):
    if len(text) == width:
        return text
    if len(text) > width:
        return text[:width-3] + '...'
    pad = ' ' * ((width - len(text))//2)
    return pad + text + pad


# TODO: open file provided by user
with open('a.bin', 'r+b') as f:
    reader = bitstream_reader.FileReader(f, 1024)
    mode = HEX_MODE

    # TODO: actual hex editor
    def main_loop(screen):
        chars_per_word = reader.get_wordsize() // mode
        words_in_line = calculate_words_in_line(chars_per_word,
                                                screen.width)
        lines = screen.height - 2  # 1 line for header and 1 for footer
        view = reader.get_view(0, lines * words_in_line)
        representation = bit_representation if mode == BIT_MODE else hex_representation

        screen.print_at(make_header_text(f.name, screen.width),
                        0, 0,
                        Screen.COLOUR_CYAN,
                        Screen.A_BOLD and Screen.A_REVERSE)

        for line_number in range(lines):
            pos = 0
            for word_number in range(words_in_line):
                screen.print_at(representation(view[line_number*words_in_line+word_number]),
                                pos, line_number+1)
                pos += chars_per_word
                screen.print_at(' ', pos, line_number+1)
                pos += 1

        while True:
            if screen.has_resized():
                screen = Screen.wrapper(main_loop)
                screen.clear()
            # screen.print_at(str(words_in_line), 0, 0)
            screen.refresh()

    Screen.wrapper(main_loop)

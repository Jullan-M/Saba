from PIL import Image, ImageDraw, ImageFont
import random


def text_wrap(text, font, imgdraw, max_width, max_height):
    # Code fetched and slightly modified from https://stackoverflow.com/questions/8257147/wrap-text-in-pil
    # Courtesy of Chris Jones
    lines = [[]]
    words = text.split(' ')
    for word in words:
        # try putting this word in last line then measure
        lines[-1].append(word)
        (w, h) = imgdraw.multiline_textsize(
            '\n'.join([' '.join(line) for line in lines]), font=font, spacing=10)
        if w > max_width:  # too wide
            # take it back out, put it on the next line, then measure again
            lines.append([lines[-1].pop()])
            (w, h) = imgdraw.multiline_textsize(
                '\n'.join([' '.join(line) for line in lines]), font=font, spacing=10)
            # too high now, cannot fit this word in, return empty string (False)
            if h > max_height:
                return ''
    return '\n'.join([' '.join(line) for line in lines])


FLAG_IMGS = ['media/sme.png', 'media/no.png', 'media/en.png']

TW_COLORS = [(29, 161, 242),
             (255, 173, 31),
             (244, 36, 94),
             (121, 75, 196),
             (244, 93, 34),
             (23, 191, 99)]

WIDTH = 1080
HEIGHT = 710

# Twitter font: https://www.cufonfonts.com/font/helvetica-neue-lt
FONT = "tahoma.ttf"
FONT_IT = "Tahoma W01 Italic.ttf"
MAX_FSIZE = 72


def examples_img(lang, word, examples):
    # examples: Array of strings
    if not examples[0]:
        return False

    img = Image.new('RGB', (WIDTH, HEIGHT), color=(21, 32, 43))
    d = ImageDraw.Draw(img)
    rn_color = random.choice(TW_COLORS)
    d.text((20, HEIGHT - 90), f"{word}", font=ImageFont.truetype(
        FONT, size=72), fill=rn_color)
    d.text((780, HEIGHT - 45), f"@WOTD_{lang}", font=ImageFont.truetype(
        FONT, size=46), fill=rn_color)

    for i, fl in enumerate(FLAG_IMGS):
        fl_img = Image.open(fl)
        img.paste(fl_img, (20, 20 + 200 * i))

        font_size = MAX_FSIZE
        text_font = ImageFont.truetype(FONT_IT, size=font_size)
        text_wrapped = text_wrap(examples[i], text_font, d, 778, 180)

        while not text_wrapped:
            font_size -= 4
            text_font = ImageFont.truetype(FONT_IT, size=font_size)
            text_wrapped = text_wrap(examples[i], text_font, d, 778, 180)

        d.text((282, 20 + 200 * i), text_wrapped,
               font=text_font, fill=(255, 255, 255), spacing=10)

    img.save(f'media/examples_{lang}.png')
    return True

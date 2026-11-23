import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageColor

import math

DEFAULT_FONT = "font/IoskeleyMonoTerm-Regular.ttf"

def shaped_gaussian_filter(shape:tuple[int, int]=(15, 15), sigma:float=2) -> np.ndarray:
    height, width = shape
    m = max(width, height)
    g = gaussian_filter(m, sigma)
    d_width = m - width
    d_height = m - height
    return g[(d_height // 2):(height + (d_height // 2)), (d_width // 2):(width + (d_width // 2))]

def gaussian_filter(size:int=15, sigma:float=3):
    x, y = np.mgrid[-size//2 + 1:size//2 + 1, -size//2 + 1:size//2 + 1]
    g = np.exp(-((x**2 + y**2)/(2.0*sigma**2)))
    return g/g.sum()

# Source - https://stackoverflow.com/a/72615170
# Posted by Sue Donhym
# Retrieved 2026-11-22, License - CC BY-SA 4.0

# Source - https://stackoverflow.com/q/68648801
# Posted by HitLuca, modified by community. See post 'Timeline' for change history
# Retrieved 2026-11-22, License - CC BY-SA 4.0

def text_to_array(
    text: str,
    font_filepath: str = DEFAULT_FONT,
    font_size: int = 15,
) -> np.ndarray:
    font = ImageFont.truetype(font_filepath, size=font_size)
    bounds = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox(
        (0, 0), text, font=font
    )
    left, _, right, _ = bounds

    x_offset = max(0, -left)
    width = math.ceil(max(font.getlength(text), right) + x_offset)
    ascent, descent = font.getmetrics()

    img = Image.new("L", (width, ascent + descent), 0)
    ImageDraw.Draw(img).text(
        (x_offset, 0), text, font=font, fill=255
    )
    return np.array(img)
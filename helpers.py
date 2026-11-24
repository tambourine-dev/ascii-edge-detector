import numpy as np
from PIL import Image, ImageFont, ImageDraw
import math
from skimage.feature import match_template
import defaults
import helpers

import matplotlib.pyplot as plt

def shaped_gaussian_filter(shape:tuple[int, int]=(15, 15)) -> np.ndarray:
    height, width = shape
    m = max(width, height)
    sigma = min(width, height) // 4
    g = gaussian_filter(m, sigma)
    d_width = m - width
    d_height = m - height
    res = g[(d_height // 2):(height + (d_height // 2)), (d_width // 2):(width + (d_width // 2))]
    plt.imshow(res)
    plt.show()
    return res

def gaussian_filter(size:int=15, sigma:float=3):
    x, y = np.mgrid[-size//2 + 1:size//2 + 1, -size//2 + 1:size//2 + 1]
    g = np.exp(-((x**2 + y**2)/(2.0*sigma**2)))
    return g/g.sum()

def text_to_array(
    text: str,
    font_filepath: str = defaults.FONT,
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


def char_likelihoods(img: np.ndarray, filter: np.ndarray) -> np.ndarray:
    height = img.shape[0] // filter.shape[0]
    width = img.shape[1] // filter.shape[1]

    result = np.zeros((height, width))

    for i in range(height):
        for j in range(width):
            partition = img[
                i * filter.shape[0]: (i + 1) * filter.shape[0],
                j * filter.shape[1]: (j + 1) * filter.shape[1],
            ]
            result[i, j] = np.max(partition * filter)

    return result


def edge_to_ascii(edge_image: np.ndarray, charset:str = defaults.CHARSET_BASIC, selection_threshold:float=defaults.SELECTION_THRESHOLD, font:str=defaults.FONT, font_size:int=defaults.FONT_SIZE) -> str:
    print("correlating characters…")
    correlation_kernels = [helpers.text_to_array(char, font, font_size) for char in charset]
    gaussian_filter = helpers.shaped_gaussian_filter(correlation_kernels[0].shape)
    correlation_results = [ match_template(edge_image, pattern) for pattern in correlation_kernels ]
    try:
        correlation_results_stacked = np.stack([char_likelihoods(result, gaussian_filter) for result in correlation_results], axis=2)
    except ValueError:
        raise ValueError("Your font does not have the same size for all characters of the character in the set. Try different characters or different monospaced font.")
    result_string = ""

    print("chosing best-match characters…")
    for i in range(correlation_results_stacked.shape[0]):
        for j in range(correlation_results_stacked.shape[1]):
            k = np.argmax(correlation_results_stacked[i, j, :])
            value = correlation_results_stacked[i, j, k]
            result_string += (
                charset[k]
                if value > selection_threshold
                else " "
            )
        result_string += "\n"

    return result_string
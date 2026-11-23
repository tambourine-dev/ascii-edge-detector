import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

import edge_detection
from helpers import edge_to_ascii
import kernels
import defaults
import numpy as np

from skimage.io import imread

from PIL import Image, ImageColor, ImageDraw, ImageFont
import math


METHOD_ALIASES = {
    "threshold": "threshold",
    "0": "threshold",
    "canny": "canny",
    "1": "canny",
}

KERNEL_ALIASES = {
    "elementary": "elementary",  
    "0": "elementary",
    "prewitt": "prewitt",        
    "1": "prewitt",
    "scharr": "scharr",          
    "2": "scharr",
    "sobel": "sobel",            
    "3": "sobel",
}


def resolve_alias(value: str, aliases: dict[str, str]) -> str:
    try:
        return aliases[value.lower()]
    except KeyError:
        raise argparse.ArgumentTypeError(
            f"invalid choice: '{value}'"
        ) from None

def parser_setup() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
            prog="ascii-edge-detector",
            description="Turn an image into ASCII or Unicode illustrations.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
    
    parser.add_argument(
        "source",
        type=Path,
        metavar="IMAGE",
        help="path to the source image"
    )
    parser.add_argument(
        "-d",
        "--destination",
        type=str,
        default="console",
        help="where to save the result"
    )
    parser.add_argument(
        "-m",
        "--method",
        type=lambda value: resolve_alias(value, METHOD_ALIASES),
        choices=("threshold", "canny"),
        default="canny",
        help="edge detection method",
    )
    parser.add_argument(
        "-k",
        "--kernel",
        type=lambda value: resolve_alias(value, KERNEL_ALIASES),
        choices=("elementary", "prewitt", "scharr", "sobel"),
        default="elementary",
        help="derivative kernel",
    ) # TODO: add support for user kernels later.
    parser.add_argument(
        "-t1",
        "--primary_threshold",
        type=float,
        default=defaults.THRESHOLD_PRIMARY,
        help="primary (gradient) threshold for edge detection"
    )
    parser.add_argument(
        "-t2",
        "--secondary_threshold",
        type=float,
        default=defaults.THRESHOLD_SECONDARY,
        help="secondary (gradient) threshold for edge detection (ignored unless using Canny)"
    )
    parser.add_argument(
        "-g",
        "--gaussian",
        nargs=2,
        type=int,
        metavar=("SIZE", "SIGMA"),
        default=(defaults.GAUSSIAN_SIZE, defaults.GAUSSIAN_SIGMA),
        help="size and sigma for Gaussian filter (ignored unless using Canny)",
    )
    parser.add_argument(
        "-fs",
        "--font_size",
        type=int,
        default=defaults.FONT_SIZE,
        help="font size in pixels"
    )
    parser.add_argument(
        "-f",
        "--font",
        type=Path,
        default=defaults.FONT,
        help="font to be used"
    )
    parser.add_argument(
        "-c",
        "--chars",
        type=str,
        default=defaults.CHARSET_BASIC,
        help="set of chars to be used for image"
    )
    parser.add_argument(
        "-ct",
        "--char_threshold",
        type=int,
        default=defaults.SELECTION_THRESHOLD,
        help="correlation threshold to cosider a given ascii"
    )
    parser.add_argument(
        "-np", "--no_preview",
        action="store_true",
        help="do not show preview of image before generating ascii illustration"
    )
    parser.add_argument(
        "-fc", "--font_color",
        type=str,
        default="#000000FF",
        help="RGBA font color in hex. (ignored unless output format is image)"
    )
    parser.add_argument(
        "-bc", "--background_color",
        type=str,
        default="#FFFFFFFF",
        help="RGBA background color in hex. (ignored unless output format is image.)"
    )
    return parser

def escape_rtf(text: str) -> str:
    parts = []
    for char in text:
        if char in "\\{}":
            parts.append("\\" + char)
        elif char == "\n":
            parts.append(r"\par" + "\n")
        elif ord(char) < 128:
            parts.append(char)
        else:
            codepoint = ord(char)
            units = (
                [codepoint] if codepoint <= 0xFFFF else [
                    0xD800 + ((codepoint - 0x10000) >> 10),
                    0xDC00 + ((codepoint - 0x10000) & 0x3FF),
                ]
            )
            for unit in units:
                parts.append(rf"\u{unit if unit < 0x8000 else unit - 0x10000}?")
    return "".join(parts)

def main() -> None:
    parser = parser_setup()
    args = parser.parse_args()

    image = np.array(imread(args.source, as_gray=True), dtype=float)
    if image is None:
        parser.error(f"could not read image: '{args.source}'")

    operator = kernels.str_to_op(args.kernel)

    print("computing derivatives…")

    print("computing edges…")
    if args.method == "threshold":
        edge_image = edge_detection.threshold(
            image,
            operator,
            thresh=args.primary_threshold
        )
    else:
        edge_image = edge_detection.canny(
            image,
            operator,
            args.gaussian[0],
            args.gaussian[1],
            args.primary_threshold,
            args.secondary_threshold
        )

    print("edge detection done.")
    if not args.no_preview:
        print("preview edge image:")
        plt.imshow(edge_image)
        plt.show()

    print("generating ascii illustration...")
    result = edge_to_ascii(
        edge_image,
        charset=args.chars,
        font=args.font,
        font_size=args.font_size
    )

    print(args.destination)
    if args.destination == "console":
        print(result)
    elif args.destination.endswith('.txt'):
        with open(args.destination, 'w') as file:
            file.write(result)
            file.close()
    elif Path(args.destination).suffix.lower() == ".rtf":
        font = ImageFont.truetype(str(args.font), args.font_size)
        font_family, _ = font.getname()
        if font_family is None:
            parser.error(f"Could not determine font family from '{args.font}'")

        font_name = escape_rtf(font_family)
        size_half_points = round(args.font_size * 1.5)  # pixels to RTF half-points

        rtf = (
            r"{\rtf1\ansi\deff0\uc1"
            rf"{{\fonttbl{{\f0\fnil {font_name};}}}}"
            rf"\f0\fs{size_half_points} "
            f"{escape_rtf(result)}"
            "}"
        )

        with open(args.destination, "w", encoding="ascii", newline="") as file:
            file.write(rtf)
    elif Path(args.destination).suffix.lower() in {
    ".png", ".jpg", ".jpeg", ".tif", ".tiff"
}:
        try:
            foreground = ImageColor.getcolor(args.font_color, "RGBA")
            background = ImageColor.getcolor(args.background_color, "RGBA")
        except ValueError as exc:
            parser.error(f"invalid image color: {exc}")

        font = ImageFont.truetype(str(args.font), args.font_size)
        rows = result.splitlines()
        ascent, descent = font.getmetrics()
        line_height = ascent + descent
        width = max(1, math.ceil(max(
            (font.getlength(row) for row in rows), default=0
        )))
        height = max(1, len(rows) * line_height)

        text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        for row_index, row in enumerate(rows):
            draw.text(
                (0, row_index * line_height),
                row,
                font=font,
                fill=foreground,
            )

        output = Image.alpha_composite(
            Image.new("RGBA", text_layer.size, background),
            text_layer,
        )

        if Path(args.destination).suffix.lower() in {".jpg", ".jpeg"}:
            if isinstance(background, int):
                parser.error("Expected an RGBA tuple for background color")

            matte = Image.new(
                "RGBA",
                output.size,
                (background[0], background[1], background[2], 255),
            )
            output = Image.alpha_composite(matte, output).convert("RGB")

        output.save(args.destination)

if __name__ == "__main__":
    mpl.rc("image", cmap="gray")
    main()
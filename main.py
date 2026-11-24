import argparse
import json
import math
import os
import string
import subprocess
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager

import edge_detection
from helpers import edge_to_ascii
import kernels
import defaults
import numpy as np

from skimage.io import imread

from PIL import Image, ImageColor, ImageDraw, ImageFont

def parse_kernel_matrix(value: str) -> np.ndarray:
    try:
        matrix = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(
            f"kernel must be a JSON matrix: {exc.msg}"
        ) from None

    if not isinstance(matrix, list) or not matrix or any(
        not isinstance(row, list) or not row for row in matrix
    ):
        raise argparse.ArgumentTypeError(
            "kernel must be a non-empty, rectangular 2D JSON matrix"
        )

    row_length = len(matrix[0])
    if any(len(row) != row_length for row in matrix):
        raise argparse.ArgumentTypeError(
            "kernel rows must all have the same number of values"
        )
    for row in matrix:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise argparse.ArgumentTypeError(
                    "kernel values must be finite numbers"
                )
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise argparse.ArgumentTypeError(
                    "kernel values must be finite numbers"
                )

    return np.asarray(matrix, dtype=float)

def parse_charset(value: str) -> str:
    charset = defaults.CHARSETS.get(value.lower(), value)
    if not charset:
        raise argparse.ArgumentTypeError(
            "charset must contain at least one character"
        )
    if len(set(charset)) != len(charset):
        raise argparse.ArgumentTypeError(
            "charset must not contain duplicate characters"
        )
    return charset

def load_monospace_font(
    font_path: Path | None,
    font_size: int,
    parser: argparse.ArgumentParser,
) -> tuple[Path, ImageFont.FreeTypeFont]:
    if font_path is None:
        try:
            font_path = Path(
                font_manager.findfont(
                    font_manager.FontProperties(family="monospace"),
                    fallback_to_default=False,
                )
            )
        except ValueError as exc:
            parser.error(f"could not find an installed monospace font: {exc}")

    try:
        font = ImageFont.truetype(str(font_path), font_size)
    except OSError as exc:
        parser.error(f"could not load font '{font_path}': {exc}")

    printable_ascii = string.ascii_letters + string.digits + string.punctuation + " "
    advances = {font.getlength(character) for character in printable_ascii}
    if len(advances) != 1:
        parser.error(f"font '{font_path}' is not monospace")

    return font_path, font

def parser_setup() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
            prog="askid",
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
        type=str,
        choices=("threshold", "canny"),
        default="canny",
        help="edge detection method",
    )
    parser.add_argument(
        "-k",
        "--kernel",
        type=str,
        choices=("elementary", "prewitt", "scharr", "sobel", "custom"),
        default="elementary",
        help="derivative kernel preset, or 'custom' to provide your own pair",
    )
    parser.add_argument(
        "--kernel-x",
        type=parse_kernel_matrix,
        metavar="JSON_MATRIX",
        help="custom horizontal derivative kernel (JSON, used with --kernel custom)",
    )
    parser.add_argument(
        "--kernel-y",
        type=parse_kernel_matrix,
        metavar="JSON_MATRIX",
        help="custom vertical derivative kernel (JSON, used with --kernel custom)",
    )
    parser.add_argument(
        "-t1",
        "--primary-threshold",
        "--primary_threshold",
        type=float,
        default=defaults.THRESHOLD_PRIMARY,
        help="primary (gradient) threshold for edge detection"
    )
    parser.add_argument(
        "-t2",
        "--secondary-threshold",
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
        "--font-size",
        "--font_size",
        type=int,
        default=defaults.FONT_SIZE,
        help="font size in pixels"
    )
    parser.add_argument(
        "-f",
        "--font",
        type=Path,
        default=None,
        help="font file to use (defaults to an installed monospace font)"
    )
    parser.add_argument(
        "-c",
        "--chars",
        type=parse_charset,
        default=defaults.CHARSET_BASIC,
        help="charset preset (minimal, basic, extended, borderbox) or custom characters"
    )
    parser.add_argument(
        "-ct",
        "--char-threshold",
        "--char_threshold",
        type=int,
        default=defaults.SELECTION_THRESHOLD,
        help="correlation threshold to cosider a given ascii"
    )
    parser.add_argument(
        "-np", "--no-preview", "--no_preview",
        action="store_true",
        help="do not show preview of image before generating ascii illustration"
    )
    parser.add_argument(
        "-fc", "--font-color", "--font_color",
        type=str,
        default="#000000FF",
        help="RGBA font color in hex. (ignored unless output format is image)"
    )
    parser.add_argument(
        "-bc", "--background-color", "--background_color",
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

def open_with_default_app(path: Path) -> None:
    resolved_path = str(path.resolve())

    if sys.platform == "win32":
        startfile = getattr(os, "startfile", None)
        if not callable(startfile):
            raise RuntimeError("opening files with the default application is unavailable")
        startfile(resolved_path)
    elif sys.platform == "darwin":
        subprocess.run(["open", resolved_path], check=True)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", resolved_path], check=True)
    else:
        raise RuntimeError(
            f"opening files with the default application is unsupported on {sys.platform}"
        )

def run(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    font_path, font = load_monospace_font(args.font, args.font_size, parser)

    image = np.array(imread(args.source, as_gray=True), dtype=float)
    if image is None:
        parser.error(f"could not read image: '{args.source}'")

    if args.kernel == "custom":
        if args.kernel_x is None or args.kernel_y is None:
            parser.error(
                "--kernel custom requires both --kernel-x and --kernel-y"
            )
        operator = kernels.Derivative_Kernels(args.kernel_x, args.kernel_y)
    else:
        if args.kernel_x is not None or args.kernel_y is not None:
            parser.error(
                "--kernel-x and --kernel-y can only be used with --kernel custom"
            )
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
        font=str(font_path),
        font_size=args.font_size
    )

    destination = Path(args.destination)
    suffix = destination.suffix.lower()
    print(f"saving to {args.destination}")
    if args.destination == "console":
        print(result)
    elif suffix == ".txt":
        with destination.open("w", encoding="utf-8") as file:
            file.write(result)
        open_with_default_app(destination)
    elif suffix == ".rtf":
        font_family, _ = font.getname()
        if font_family is None:
            parser.error(f"Could not determine font family from '{font_path}'")

        font_name = escape_rtf(font_family)
        size_half_points = round(args.font_size * 1.5)  # pixels to RTF half-points

        rtf = (
            r"{\rtf1\ansi\deff0\uc1"
            rf"{{\fonttbl{{\f0\fnil {font_name};}}}}"
            rf"\f0\fs{size_half_points} "
            f"{escape_rtf(result)}"
            "}"
        )

        with destination.open("w", encoding="ascii", newline="") as file:
            file.write(rtf)
        open_with_default_app(destination)
    elif suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        try:
            foreground = ImageColor.getcolor(args.font_color, "RGBA")
            background = ImageColor.getcolor(args.background_color, "RGBA")
        except ValueError as exc:
            parser.error(f"invalid image color: {exc}")

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

        if suffix in {".jpg", ".jpeg"}:
            if isinstance(background, int):
                parser.error("Expected an RGBA tuple for background color")

            matte = Image.new(
                "RGBA",
                output.size,
                (background[0], background[1], background[2], 255),
            )
            output = Image.alpha_composite(matte, output).convert("RGB")

        output.save(destination)
        open_with_default_app(destination)
    else:
        parser.error(
            "unsupported destination format; use console, .txt, .rtf, "
            ".png, .jpg, .jpeg, .tif, or .tiff"
        )


def main() -> None:
    parser = parser_setup()
    args = parser.parse_args()
    try:
        run(args, parser)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.error(f"could not process image: {exc}")

if __name__ == "__main__":
    mpl.rc("image", cmap="gray")
    main()
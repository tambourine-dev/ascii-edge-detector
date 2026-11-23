# ascii-edge-detector
This terminal-based python script turns your images into ascii or unicode (box-drawing character) illustrations.

Use `--kernel custom` to supply a pair of derivative kernels as JSON matrices:

```sh
python main.py image.jpg --kernel custom \
  --kernel-x '[[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]' \
  --kernel-y '[[-1, -2, -1], [0, 0, 0], [1, 2, 1]]'
```

Both matrices must be non-empty, rectangular 2D arrays of finite numbers.

Choose a built-in character set with `--chars minimal`, `basic` (the default),
`extended`, or `borderbox`. To provide your own, pass the characters directly,
for example `--chars '@#.'`. Character sets must be non-empty and cannot repeat
characters.

The default font is selected from available monospace fonts on your system.
Use `--font /path/to/font.ttf` to choose a specific font file; the program
rejects fonts that are not fixed-width.

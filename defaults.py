# font defaults
FONT = "font/IoskeleyMonoTerm-Regular.ttf"
FONT_SIZE = 15

# gaussian defaults

GAUSSIAN_SIZE = 15
GAUSSIAN_SIGMA = 3

# threshold defaults

THRESHOLD_PRIMARY = 0.2
THRESHOLD_SECONDARY = 0.02

# charsets

CHARSET_MINIMAL = "_-/\\|"
CHARSET_BASIC = "_-()[]{}/\\<>|"
CHARSET_EXTENDED = "_-:.\"()[]{}§@*/\\#%`+<>|~≈¤$078HIJLnoOSTuVwXY"
CHARSET_BORDERBOX = "─│┌┐└┘├┤┬┴┼╭╮╯╰╱╲╳╴╵╶╷"

CHARSETS = {
    "minimal": CHARSET_MINIMAL,
    "basic": CHARSET_BASIC,
    "extended": CHARSET_EXTENDED,
    "borderbox": CHARSET_BORDERBOX,
}

# THRESHOLD NEEDED TO SELECT ASCII CHAR

SELECTION_THRESHOLD = 0.01
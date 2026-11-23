import numpy as np
import helpers


ascii_values = "{}[]()<>/\\|-_"

ascii_correlations = list(map(helpers.text_to_array, ascii_values))

shape = ascii_correlations[0].shape
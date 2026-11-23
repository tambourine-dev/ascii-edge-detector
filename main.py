from skimage.io import imread
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import scipy

import threshold
import canny
import kernels
import correlations
import helpers

from skimage.feature import match_template

mpl.rc('image', cmap='gray')

def main():
    print("hello_world")

if __name__ == "__main__":
    main()

image = np.array(imread("images/ta_moulton_barn.jpg", as_gray=True), dtype=float)

operator = kernels.str_to_op("elementary")

edge_image = canny.canny(image, operator, thresh_high=0.2, thresh_low=0.1)

# plt.imshow(edge_image)
# plt.show()

print("edge_detection done")
# selection_bias= helpers.gaussian_filter()

def scan (img:np.ndarray, filter: np.ndarray) -> np.ndarray:
    
    height = img.shape[0] // filter.shape[0]
    width = img.shape[1] // filter.shape[1]

    res = np.zeros((height, width))
    for i in range(height):
        for j in range(width):
            partition = img[(i*filter.shape[0]):(i + 1)*filter.shape[0],j*filter.shape[1]:(j + 1)*filter.shape[1]]
            weighted = partition * filter
            res[i, j] = np.max(weighted)
    return res

gaussian_filter = helpers.shaped_gaussian_filter(correlations.shape)

# plt.imshow(gaussian_filter)
# plt.show()


def edge_to_ascii():
    correlated = list(map(lambda x: match_template(edge_image, x), correlations.ascii_correlations))
    components = list(map(lambda x: scan(x, gaussian_filter), correlated))
    components_stacked = np.stack(components, axis=2)
    SELECTION_THRESH = 0.01
    # result = np.empty(components_stacked.shape[0:2])
    result_string = ""
    # print(np.average(components_stacked))
    # print(np.max(components_stacked))
    for i in range(components_stacked.shape[0]):
        for j in range(components_stacked.shape[1]):
            k = np.argmax(components_stacked[i, j, :])
            char = correlations.ascii_values[k] if components_stacked[i, j, k] > SELECTION_THRESH else " "
            # result[i, j] = char
            result_string += char
        result_string += "\n"
    print(result_string)

edge_to_ascii()

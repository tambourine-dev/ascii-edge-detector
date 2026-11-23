import scipy
import numpy as np
import kernels


def gradient_magnitude(img, operator:kernels.Derivative_Kernels):
  dx2 = scipy.ndimage.convolve(img,operator.kx) ** 2
  dy2 = scipy.ndimage.convolve(img, operator.ky) ** 2
  return np.sqrt(dx2 + dy2)

def gradient_magnitude_threshold(img, operator:kernels.Derivative_Kernels, thresh:float=0.16):
  return np.where(gradient_magnitude(img, operator) > thresh, 1, 0)
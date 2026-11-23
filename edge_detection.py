import numpy as np
import scipy
import defaults
import kernels
import helpers

import scipy
import kernels

import matplotlib.pyplot as plt

def gradient_magnitude(img:np.ndarray, operator:kernels.Derivative_Kernels) -> np.ndarray:
  print("derivin…")
  dx2 =scipy.ndimage.convolve(img,operator.kx) ** 2
  dy2 =scipy.ndimage.convolve(img, operator.ky) ** 2
  return np.sqrt(dx2 + dy2)

def threshold(img:np.ndarray, operator:kernels.Derivative_Kernels, thresh:float=0.16) -> np.ndarray:
  return np.where(gradient_magnitude(img, operator) > thresh, 1, 0)

def quantize(x:float) -> float:
  x = x / np.pi
  if (x <= 0):
    x = 1 + x
  return round(x * 3)

def get(arr:np.ndarray, i:int, j:int, fallback:float = 0) -> float:
  try:
    return arr[i, j]
  except IndexError:
    return fallback

def surpress(a:float, b:float, c:float, high:float=0.8, low:float=0.4) -> float:
  return a if a >= max(b, c) else 0

def nonmaximum_surperession(m:np.ndarray, a:np.ndarray) -> np.ndarray:
  res = np.zeros(m.shape)
  for i in range(res.shape[0]):
    for j in range(res.shape[1]):
      match a[i, j]:
        case 0: # horizontal
          res[i, j] = surpress(m[i, j], get(m, i-1, j), get(m, i+1, j))
        case 1: # primary diagonal
          res[i, j] = surpress(m[i, j], get(m, i-1, j-1), get(m, i+1, j+1))
        case 2: # vertical
          res[i, j] = surpress(m[i, j], get(m, i, j-1), get(m, i, j+1))
        case 3: # secondary vertical
          res[i, j] = surpress(m[i, j], get(m, i-1, j+1), get(m, i+1, j-1))
  return res

def neighborhood(shape:tuple[int, int], i:int, j:int) -> list[tuple[int, int]]:
  n = []
  for y in [i-1, i, i+1]:
    for x in [j-1, j, j+1]:
      if 0 <= y < shape[0] and 0 <= x < shape[1]:
        n.append([y, x])
  return n

def hysteresis(img:np.ndarray, h:float, l:float) -> np.ndarray:
  # mark high regions
  res = np.zeros(img.shape)
  q = []
  for i in range(res.shape[0]):
    for j in range(res.shape[1]):
      if img[i, j] >= h:
        res[i, j] = 1
        q.append([i, j])

  while len(q) > 0:
    [i, j] = q.pop()
    for [y, x] in neighborhood(img.shape, i, j):
      if res[y, x] == 1: continue # already explored / in queue
      elif img[y, x] >= l:
        res[y, x] = 1
        q.append([y, x])
  return res

def canny(
    img:np.ndarray, 
    operator:kernels.Derivative_Kernels, 
    gauss_size: int=defaults.GAUSSIAN_SIZE, 
    gauss_sigma: int= defaults.GAUSSIAN_SIGMA, 
    thresh_1:float =  defaults.THRESHOLD_PRIMARY, 
    thresh_2:float = defaults.THRESHOLD_SECONDARY
    ) -> np.ndarray:
   print("blurring…")
   g = helpers.gaussian_filter(gauss_size, gauss_sigma)
   blurred = scipy.ndimage.convolve(img, g)
   print("deriving…")
   dx = scipy.ndimage.convolve(blurred, operator.kx)
   dy = scipy.ndimage.convolve(blurred, operator.ky)
   print("quantizing…")
   gradient_norm = np.sqrt(dx**2 + dy**2)
   gradient_norm = gradient_norm / np.max(gradient_norm)
   gradient_angle = np.arctan2(dx, dy)
   quantized_gradient_angle = np.vectorize(quantize)(gradient_angle)
   print("surpressing…")
   nonmaximum_surpressed = nonmaximum_surperession(gradient_norm, quantized_gradient_angle)
   print("histerizing…")
   hysterisized = hysteresis(nonmaximum_surpressed, thresh_1, thresh_2)
   return hysterisized

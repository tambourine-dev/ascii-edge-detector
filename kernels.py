import numpy as np

class Derivative_Kernels:
    def __init__(self, kx, ky):
        self.kx = kx
        self.ky = ky

# elementary derivative kernels
elementary = Derivative_Kernels(
    np.array([[-1, 1]]), 
    np.array([[-1], [1]])
)

# sobell derivative kernels

sobel = Derivative_Kernels(
    np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]),
    np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
)

# prewitt derivative kernels

prewitt = Derivative_Kernels(
    np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]]),
    np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])
)

# scharr oderivative kernels

scharr = Derivative_Kernels(
    [[-3, 0, 3], [-10, 0, 10], [-3, 0, 3]], 
    [[3, 10, 3], [0, 0, 0], [-3, -10, -3]]
)

def str_to_op(str:str) -> Derivative_Kernels:
    match str.lower():
         case 'elementary':
           return elementary
         case 'sobel':
           return sobel
         case 'prewitt':
           return prewitt
         case 'scharr':
           return scharr
         case _:
           raise ValueError(f"'{str}' is not a predefined operator, try 'elementary', 'sobell', 'prewitt' or 'scharr' (default is 'elementary')")
       
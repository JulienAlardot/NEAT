from numba import cuda
from numba import jit
import math

@jit(nopython=True)
def Relu(x):
    return max(0., x)


@jit(nopython=True)
def LRelu(x, epsilon=1e-8):
    return max(epsilon * x, x)


@jit(nopython=True)
def Elu(x, alpha=1.):
    return alpha*((math.e**x)-1) if x < 0 else x


@jit(nopython=True)
def Relu_backward(x):
    return 0 if x < 0 else 1

@jit(nopython=True)
def LRelu_backward(x, epsilon=1e-8):
    return epsilon if x < 0 else 1

@jit(nopython=True)
def Elu_backward(x, alpha=2.0):
    return alpha*(math.e**x) if x < 0 else 1

# if __name__ == "__main__"

    # try:
    #     cuda.compile_ptx(f, [])
    # except:
    #     pass

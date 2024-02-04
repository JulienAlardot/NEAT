import math
import sys

EPSILON = sys.float_info.epsilon


def sigmoid(x):
    return 1.0 / (1.0 + math.e ** (-4.9 * x))


def relu(x):
    return max(0, x)


def leaky_relu(x):
    if x > 0:
        return x
    return EPSILON * x

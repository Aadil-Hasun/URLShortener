import random
import sys
base62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def long_to_short():
    short_string = ''
    for i in range(7):
        index = random.randint(0, sys.maxsize)%62
        short_string = base62[index] + short_string
    return short_string




"""
    maths package
"""


def atoi(string):
    """ Atoi stands for ASCII to Integer Conversion """
    res = 0

    # Iterate through all characters of input and update result
    for i in range(len(string)):
        res = res * 10 + (ord(string[i]) - ord('0'))

    return res


def Adjustment(a, b):
    """ Adjustment contains rule of three for calculating an integer given another integer representing a percentage """
    return (a * b) / 100

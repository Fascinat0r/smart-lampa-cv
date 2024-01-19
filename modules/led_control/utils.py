import colorsys


def value_to_temp(x):
    return min(255, 0.00000743735 * (x ** 3) - 0.00284964 * (x ** 2) + 0.00638755 * x + 255.00), \
        0.5583 * x + 55.743, \
        min(255, -0.0000316107 * (x ** 3) + 0.0120876 * (x ** 2) - 0.0268269 * x + 5.026)


def value_to_color(x):
    return colorsys.hsv_to_rgb(x / 255, 1, 1)

from enum import Enum


class LedAction(Enum):
    OFF = 0
    ON = 1

    MODE_TEMP = 2
    MODE_COLOR = 3
    MODE_DYNAMIC_COLOR = 4
    MODE_EFFECTS = 5

    BRIGHTNESS_UP = 6
    BRIGHTNESS_DOWN = 7

    VALUE_UP = 8
    VALUE_DOWN = 9



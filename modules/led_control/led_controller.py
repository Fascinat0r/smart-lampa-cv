from PIL import ImageColor

from config.settings import LED_NUM, BRIGHTNESS_DELTA, VALUE_DELTA
from main_controller.LampMode import LampMode
from modules.led_control.LedActions import LedAction
from modules.led_control.utils import value_to_temp, value_to_color

spidev_import = False
try:
    import ws2812
    import spidev

    spidev_import = True
except ImportError:
    print("Led_Controller: Can't import spidev")


class LedController:
    def __init__(self, pipe):
        self.action = None
        self.reactions = None
        self.brightness = 255
        self.values = [0] * len(LampMode)
        self.mode: LampMode = LampMode.LIGHT_TEMPERATURE
        self.last_led_sequence = [[0, 0, 0]] * LED_NUM

        self.is_on = False

        self.pipe = pipe
        self.spi = None
        if spidev_import:
            # Initialize SPI device
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)
        self.setup_reactions()
        self.update()

    def setup_reactions(self):
        pass
        self.reactions = {
            LedAction.OFF: self.power_off,
            LedAction.ON: self.power_on,
            LedAction.MODE_TEMP: self.set_mode,
            LedAction.MODE_COLOR: self.set_mode,
            LedAction.MODE_DYNAMIC_COLOR: self.set_mode,
            LedAction.MODE_EFFECTS: self.set_mode,

            LedAction.BRIGHTNESS_UP: self.brightness_up,
            LedAction.BRIGHTNESS_DOWN: self.brightness_down,
            #
            LedAction.VALUE_UP: self.value_up,
            LedAction.VALUE_DOWN: self.value_down,
        }

    def power_on(self):
        if self.is_on:
            self.turn_off()
            self.is_on = False

    def power_off(self):
        if not self.is_on:
            self.fill(self.last_led_sequence)
            self.is_on = True

    def set_mode(self):
        self.mode = self.action
        self.update()
        pass

    def brightness_up(self):
        self.brightness = min(self.brightness + BRIGHTNESS_DELTA, 255)
        print('Led_Controller: brightness ', self.brightness)
        self.update()

    def brightness_down(self):
        self.brightness = max(self.brightness - BRIGHTNESS_DELTA, 0)
        print('Led_Controller: brightness ', self.brightness)
        self.update()

    def value_up(self):
        self.values[self.mode.value] = min(self.values[self.mode.value] + VALUE_DELTA, 255)
        print('Led_Controller: value ', self.values[self.mode.value])
        self.update()

    def value_down(self):
        self.values[self.mode.value] = max(self.values[self.mode.value] - VALUE_DELTA, 0)
        print('Led_Controller: value ', self.values[self.mode.value])
        self.update()

    def fill(self, led_sequence):
        """
        Fills the LED strip with a sequence of RGB colors.

        Args:
        led_sequence (list): A list of RGB tuples, each representing the color for an LED.

        Raises:
        ValueError: If the length of led_sequence does not match the expected LED_NUM.
        """
        # Check if the length of the input sequence matches the number of LEDs
        if len(led_sequence) != LED_NUM:
            raise ValueError(
                f"Led_Controller: An array of size {LED_NUM} was expected, an array of size {len(led_sequence)} was received.")
        self.last_led_sequence = led_sequence
        koef_brightness = self.brightness / 255
        led_sequence = [[item * koef_brightness for item in sublist] for sublist in led_sequence]
        # Send the color data to the LED strip
        if self.spi:
            ws2812.write2812(self.spi, led_sequence)
        else:
            print("Led_Controller: OUT: ", led_sequence)

    def fill_hex_color(self, hex_color: str):
        """
        Fills the LED strip with a single color specified in hexadecimal format.

        Args:
        hex_color (str): The color in hexadecimal format (e.g., "#FF5733").
        """
        # Convert hex color to RGB tuple
        color = ImageColor.getcolor(hex_color, "RGB")

        # Fill the LED strip with the converted RGB color
        self.fill_color(*color)

    def fill_color(self, R: int, G: int, B: int):
        """
        Fills the LED strip with a single RGB color.

        Args:
        R (int): Red component of the color (0-255).
        G (int): Green component of the color (0-255).
        B (int): Blue component of the color (0-255).
        """
        # Create a color data sequence for the entire strip
        data = [[G, R, B]] * LED_NUM

        # Send the color data to the LED strip
        self.fill(data)

    def turn_off(self):
        """
        Turns off all LEDs on the strip.
        """
        # Send an off command to all LEDs
        if self.spi:
            ws2812.off_leds(self.spi, LED_NUM)

    def update(self):
        match self.mode:
            case LampMode.LIGHT_TEMPERATURE:
                color = value_to_temp(self.values[LampMode.LIGHT_TEMPERATURE.value])
                self.fill_color(*color)
            case LampMode.COLORED_LIGHT:
                color = value_to_color(self.values[LampMode.COLORED_LIGHT.value])
                self.fill_color(*color)
            case LampMode.DYNAMIC_COLOR:
                pass
            case LampMode.EFFECTS:
                pass

    def run(self):
        print('Led Controller: Running', flush=True)
        while True:
            try:
                if self.pipe.poll():
                    action = self.pipe.recv()
                    print(f'Led_Controller: got {action}', flush=True)
                    if action in self.reactions:
                        self.action = action
                        self.reactions[action]()
            except Exception as e:
                print("Led Controller: ", e.args)


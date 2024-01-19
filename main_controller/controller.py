# consume work
import time
from multiprocessing.connection import Connection
from threading import Thread

from config.settings import LED_CMD_DELAY
from main_controller.LampMode import LampMode
from modules.button_control.ButtonActions import ButtonAction
from modules.led_control.LedActions import LedAction


# Main controller process
class MainController:
    def __init__(self, b_pipe: Connection, l_pipe: Connection):
        self.changing_led = None
        self.led_thread = None
        self.button_reactions = None
        self.button_pipe = b_pipe
        self.led_pipe = l_pipe
        self.current_mode = LampMode.LIGHT_TEMPERATURE
        self.setup_reactions()

    def setup_reactions(self):
        self.button_reactions = {
            ButtonAction.L_CLICK: self.toggle_mode_backward,
            ButtonAction.R_CLICK: self.toggle_mode_forward,
            ButtonAction.L_HOLD: self.start_brightness_down,
            ButtonAction.R_HOLD: self.start_brightness_up,
            ButtonAction.L_REL_HOLD: self.stop_change,
            ButtonAction.R_REL_HOLD: self.stop_change,
            ButtonAction.L_CLICK_HOLD: self.start_intensity_down,
            ButtonAction.R_CLICK_HOLD: self.start_intensity_up,
            ButtonAction.L_SWIPE: self.swipe_function,
            ButtonAction.R_SWIPE: self.swipe_function
        }

    def toggle_mode_forward(self):
        self.current_mode = LampMode((self.current_mode.value % len(LampMode)) + 1)
        print(f"mode {self.current_mode}")

    def toggle_mode_backward(self):
        value = self.current_mode.value - 1
        if value < 1:
            value = len(LampMode)
        self.current_mode = LampMode(value)
        print(f"mode {self.current_mode}")

    def start_brightness_up(self):
        # Start a new thread for brightness up
        self.led_thread = Thread(target=self._led_change, args=(LedAction.BRIGHTNESS_UP,))
        self.led_thread.start()

    def start_brightness_down(self):
        # Start a new thread for brightness down
        self.led_thread = Thread(target=self._led_change, args=(LedAction.BRIGHTNESS_DOWN,))
        self.led_thread.start()

    def _led_change(self, action):
        self.changing_led = True
        while self.changing_led:
            self.led_pipe.send(action)
            print("change led:", action)
            time.sleep(LED_CMD_DELAY)

    def stop_change(self):
        # Stop the brightness change
        self.changing_led = False
        if hasattr(self, 'led_thread'):
            self.led_thread.join()

    def start_intensity_up(self):
        self.led_thread = Thread(target=self._led_change, args=(LedAction.VALUE_UP,))
        self.led_thread.start()

    def start_intensity_down(self):
        self.led_thread = Thread(target=self._led_change, args=(LedAction.VALUE_DOWN,))
        self.led_thread.start()
    
    def swipe_function(self):
        # Placeholder for swipe function
        pass

    def run(self):
        print('Main Controller: Running', flush=True)
        while True:
            if self.button_pipe.poll():
                action = ButtonAction(self.button_pipe.recv())
                print(f'>Main Controller got {action}', flush=True)
                if action in self.button_reactions:
                    self.button_reactions[action]()

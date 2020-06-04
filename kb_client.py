import dbus
import evdev
import keymap
from time import sleep

HID_DBUS = 'org.yaptb.btkbservice'
HID_SRVC = '/org/yaptb/btkbservice'


class Kbrd:
    """
    Take the events from a physically attached keyboard and send the
    HID messages to the keyboard D-Bus server.
    """
    def __init__(self):
        self.target_length = 6
        self.mod_keys = 0b00000000
        self.pressed_keys = []
        self.have_kb = False
        self.dev = None
        self.bus = dbus.SystemBus()
        self.btkobject = self.bus.get_object(HID_DBUS,
                                             HID_SRVC)
        self.btk_service = dbus.Interface(self.btkobject,
                                          HID_DBUS)
        self.wait_for_keyboard()

    def wait_for_keyboard(self, event_id=0):
        """
        Connect to the input event file for the keyboard.
        Can take a parameter of an integer that gets appended to the end of
        /dev/input/event
        :param event_id: Optional parameter if the keyboard is not event0
        """
        while not self.have_kb:
            try:
                # try and get a keyboard - should always be event0 as
                # we're only plugging one thing in
                self.dev = evdev.InputDevice('/dev/input/event{}'.format(
                    event_id))
                self.have_kb = True
            except OSError:
                print('Keyboard not found, waiting 3 seconds and retrying')
                sleep(3)
            print('found a keyboard')

    def update_mod_keys(self, mod_key, value):
        """
        Which modifier keys are active is stored in an 8 bit number.
        Each bit represents a different key. This method takes which bit
        and its new value as input
        :param mod_key: The value of the bit to be updated with new value
        :param value: Binary 1 or 0 depending if pressed or released
        """
        self.mod_keys = value << mod_key

    def update_keys(self, norm_key, value):
        if value < 1:
            self.pressed_keys.remove(norm_key)
        elif norm_key not in self.pressed_keys:
            self.pressed_keys.insert(0, norm_key)
        len_delta = self.target_length - len(self.pressed_keys)
        if len_delta < 0:
            self.pressed_keys = self.pressed_keys[:len_delta]
        elif len_delta > 0:
            self.pressed_keys.extend([0] * len_delta)

    @property
    def state(self):
        """
        property with the HID message to send for the current keys pressed
        on the keyboards
        :return: bytes of HID message
        """
        return [0xA1, 0x01, self.mod_keys, 0, *self.pressed_keys]

    def send_keys(self):
        self.btk_service.send_keys(self.state)

    def event_loop(self):
        """
        Loop to check for keyboard events and send HID message
        over D-Bus keyboard service when they happen
        """
        print('Listening...')
        for event in self.dev.read_loop():
            # only bother if we hit a key and its an up or down event
            if event.type == evdev.ecodes.EV_KEY and event.value < 2:
                key_str = evdev.ecodes.KEY[event.code]
                mod_key = keymap.modkey(key_str)
                if mod_key > -1:
                    self.update_mod_keys(mod_key, event.value)
                else:
                    self.update_keys(keymap.convert(key_str), event.value)
            self.send_keys()


if __name__ == '__main__':
    print('Setting up keyboard')
    kb = Kbrd()

    print('starting event loop')
    kb.event_loop()

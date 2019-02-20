"""directkeys.py

Handle the fake inputs for the mouse and the keyboard (on Windows).

Arise from a SO answer at stackoverflow.com/questions/13564851/generate-keyboard-events
See official documentation (with key codes) at msdn.microsoft.com/en-us/library/dd375731
https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-mouse_event
"""


import ctypes
import time

from ctypes import wintypes


user32 = ctypes.WinDLL('user32', use_last_error=True)

################################################################################

# inputs
INPUT_MOUSE                 = 0
INPUT_KEYBOARD              = 1
INPUT_HARDWARE              = 2

# keyboard events
KEYEVENTF_EXTENDEDKEY       = 0x0001
KEYEVENTF_KEYUP             = 0x0002
KEYEVENTF_UNICODE           = 0x0004
KEYEVENTF_SCANCODE          = 0x0008

# mouse events
WHEEL_DELTA                 = 120
XBUTTON1                    = 0x0001
XBUTTON2                    = 0x0002
MOUSEEVENTF_ABSOLUTE        = 0x8000
MOUSEEVENTF_HWHEEL          = 0x01000
MOUSEEVENTF_MOVE            = 0x0001
MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000
MOUSEEVENTF_LEFTDOWN        = 0x0002
MOUSEEVENTF_LEFTUP          = 0x0004
MOUSEEVENTF_RIGHTDOWN       = 0x0008
MOUSEEVENTF_RIGHTUP         = 0x0010
MOUSEEVENTF_MIDDLEDOWN      = 0x0020
MOUSEEVENTF_MIDDLEUP        = 0x0040
MOUSEEVENTF_VIRTUALDESK     = 0x4000
MOUSEEVENTF_WHEEL           = 0x0800
MOUSEEVENTF_XDOWN           = 0x0080
MOUSEEVENTF_XUP             = 0x0100
MAPVK_VK_TO_VSC             = 0

# mouse information
MOUSE_RESOLUTION            = 65535

# screen information
SCREEN_RESOLUTION           = 1920, 1080

# keys
UP                          = 0x26
DOWN                        = 0x28
A                           = 0x41

################################################################################

# C struct definitions

wintypes.ULONG_PTR = wintypes.WPARAM

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",          wintypes.LONG),
                ("dy",          wintypes.LONG),
                ("mouseData",   wintypes.DWORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",         wintypes.WORD),
                ("wScan",       wintypes.WORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        # some programs use the scan code even if KEYEVENTF_SCANCODE
        # isn't set in dwFflags, so attempt to map the correct code.
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk, MAPVK_VK_TO_VSC, 0)

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type",   wintypes.DWORD),
                ("_input", _INPUT))

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

LPINPUT = ctypes.POINTER(INPUT)

def _check_count(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return args

user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (wintypes.UINT, # nInputs
                             LPINPUT,       # pInputs
                             ctypes.c_int)  # cbSize

################################################################################

# functions

def _send(event):
    """ Call WinAPI to perform an input event.

    """

    user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event))

def query_mouse_position():
    """ Returns the current (absolute) cursor position.

    @return point: data structure with two fields .x and .y
    """

    point = POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return point

def press(key_code):
    """ Sends KeyDown event.

    @param key_code: hexadecimal code of key (see doc)
    """

    _send(INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=key_code)))

def release(key_code):
    """ Sends KeyUp event.

    @param key_code: hexadecimal code of key (see doc)
    """

    _send(INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=key_code, dwFlags=KEYEVENTF_KEYUP)))

def tap(key_code, delay=0):
    """ Sends KeyDown event and then KeyUp.

    @param key_code: hexadecimal code of key (see doc)
    @param delay: time between press and release (in seconds)
    """

    press(key_code)
    time.sleep(delay)
    release(key_code)

def clic(x, y, mode=0, delay=0):
    """ Send mouse event.

    @param x: x-position (pixel-wise, left to right)
    @param y: y-position (pixel-wise, top to bottom)
    @param mode: 0 (move-only), 1 (left-click), 2 (right-click)
    @param delay: time between MouseDown and MouseUp events (in seconds)
    """

    dx = ctypes.c_long(int(x * MOUSE_RESOLUTION / SCREEN_RESOLUTION[0]))
    dy = ctypes.c_long(int(y * MOUSE_RESOLUTION / SCREEN_RESOLUTION[1]))

    base_flags = MOUSEEVENTF_MOVE + MOUSEEVENTF_ABSOLUTE
    flags = 0x0, 0x0
    if mode == 1:
        flags = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
    elif mode == 2:
        flags = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP

    event_down = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(dx=dx, dy=dy, dwFlags=base_flags+flags[0]))
    event_up = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(dwFlags=flags[1]))

    _send(event_down)
    time.sleep(delay)
    _send(event_up)


def drag(x1, y1, x2, y2):

    dx1 = ctypes.c_long(int(x1 * MOUSE_RESOLUTION / SCREEN_RESOLUTION[0]))
    dy1 = ctypes.c_long(int(y1 * MOUSE_RESOLUTION / SCREEN_RESOLUTION[1]))
    dx2 = ctypes.c_long(int(x2 * MOUSE_RESOLUTION / SCREEN_RESOLUTION[0]))
    dy2 = ctypes.c_long(int(y2 * MOUSE_RESOLUTION / SCREEN_RESOLUTION[1]))

    base_flags = MOUSEEVENTF_MOVE + MOUSEEVENTF_ABSOLUTE
    event_down = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(dx=dx1, dy=dy1, dwFlags=base_flags+MOUSEEVENTF_LEFTDOWN))
    event_move1 = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(dwFlags=MOUSEEVENTF_MOVE))
    event_move2 = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(dx=0x10, dy=0x20, dwFlags=MOUSEEVENTF_MOVE))
    event_move3 = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(dx=dx2, dy=dy2, dwFlags=base_flags))
    event_up = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(dx=dx2, dy=dy2, dwFlags=base_flags+MOUSEEVENTF_LEFTUP))

    _send(event_down)
    time.sleep(.1)
    _send(event_move1)
    time.sleep(.1)
    _send(event_move2)
    time.sleep(.1)
    _send(event_move3)
    time.sleep(.1)
    _send(event_up)
    time.sleep(.1)


if __name__ == "__main__":
    print(__doc__)
    tap(A)
    import random
    for i in range(5000):
        clic(random.randint(0, SCREEN_RESOLUTION[0]),
             random.randint(0, SCREEN_RESOLUTION[1]))

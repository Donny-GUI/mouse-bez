import pyautogui
import os
import subprocess
from time import sleep
from random import randint, choice
from math import ceil
from multiprocessing import Process
import ctypes
from typing import List, Tuple, Callable, Any
from PIL import Image  # Ensure to import PIL for image handling
from itertools import tee  # For removing duplicates
from typing import Union, TypeVar, Iterator, List, Tuple, Dict, Callable

pyautogui.MINIMUM_DURATION = 0.01
# WORKING DIRECTORY
CWD = os.path.dirname(os.path.realpath(__file__))

def remove_dups(seq: List[Any]) -> List[Any]:
    """
    Removes duplicates from a list, preserving order.

    Parameters
    ----------
    seq : list
        List to remove duplicates from.

    Returns
    -------
    list
        List with duplicates removed.
    """
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]

def draw_points(points: List[Tuple[int, int]], width: int = 2000, height: int = 2000) -> None:
    """
    Draws yellow crosses on a (default 2000x2000px) image for all coordinates in the "points" argument
    and saves to CWD as out-YYYY-MM-DD_HH-MM-SS.png.

    Parameters
    ----------
    points : list of tuples
        List of (x, y) coordinates to draw crosses at.
    width : int
        Width of the image (default 2000).
    height : int
        Height of the image (default 2000).
    """
    img = Image.new("RGB", (width, height))
    pix = img.load()

    try:
        for coords in points:
            pix[coords[0], coords[1]] = (255, 255, 0)
            pix[coords[0] + 1, coords[1] + 1] = (255, 255, 0)
            pix[coords[0] + 1, coords[1] - 1] = (255, 255, 0)
            pix[coords[0] - 1, coords[1] + 1] = (255, 255, 0)
            pix[coords[0] - 1, coords[1] - 1] = (255, 255, 0)

        img.save(os.path.join(CWD, 'tmp', f'out-{strftime("%Y-%m-%d_%H-%M-%S", gmtime())}.png'))
    except Exception as e:
        print(f"Error saving image: {e}")

def real_click() -> None:
    """
    Clicks the mouse with realistic errors:
    occasional accidental right click, occasional double click, and occasional no click.
    """
    if randint(1, 19) != 1:
        sleep(93 / randint(83, 201))
        pyautogui.click()
    else:
        tmp_rand = randint(1, 3)
        if tmp_rand == 1:
            # Double click
            pyautogui.click()
            sleep(randint(43, 113) / 1000)
            pyautogui.click()
        elif tmp_rand == 2:
            pyautogui.click(button='right')

def move_to_img(img_name: str, deviation: int, speed: int) -> bool:
    """
    Moves the mouse to a random pixel on the specified image.

    Parameters
    ----------
    img_name : str
        Name of the input image (excluding file extension).
    deviation : int
        Maximum deviation for the movement.
    speed : int
        Speed of the movement (lower is faster).

    Returns
    -------
    bool
        True if the image was found and movement was successful, otherwise False.
    """
    loc = list(pyautogui.locateAllOnScreen(os.path.join(CWD, 'img', f'{img_name}.png')))
    init_pos = pyautogui.position()

    if loc:
        loc = choice(loc)
        x_bounds = loc[0] + randint(0, loc[2])
        y_bounds = loc[1] + randint(0, loc[3])

        if speed == 0:
            os.system(f'xdotool mousemove {x_bounds} {y_bounds}')
            sleep(randint(2, 9) / 100)
            pyautogui.click()
        else:
            move(mouse_bez(init_pos, (x_bounds, y_bounds), deviation, speed))

        return True
    else:
        print("Can't find location")
        return False

def move_to_area(x: int, y: int, width: int, height: int, deviation: int, speed: int) -> None:
    """
    Moves the mouse to a random point within the specified area.

    Parameters
    ----------
    x : int
        X-coordinate of the top-left corner.
    y : int
        Y-coordinate of the top-left corner.
    width : int
        Width of the area.
    height : int
        Height of the area.
    deviation : int
        Maximum deviation for the movement.
    speed : int
        Speed of the movement (lower is faster).
    """
    init_pos = pyautogui.position()

    x_coord = x + randint(0, width)
    y_coord = y + randint(0, height)

    move(mouse_bez(init_pos, (x_coord, y_coord), deviation, speed))

def pascal_row(n: int) -> List[int]:
    """
    Returns the nth row of Pascal's Triangle as a list of integers.

    Parameters
    ----------
    n : int
        The row number to calculate, starting at 0.

    Returns
    -------
    list
        The nth row of Pascal's Triangle as a list of integers.
    """
    result = [1]
    x, numerator = 1, n
    for denominator in range(1, n//2 + 1):
        x *= numerator
        x //= denominator
        result.append(x)
        numerator -= 1
    if n % 2 == 0:
        result.extend(reversed(result[:-1]))
    else:
        result.extend(reversed(result))
    return result

def make_bezier(xys: List[Tuple[float, float]]) -> Callable[[List[float]], List[Tuple[float, float]]]:
    """
    Returns a function that takes a sequence of floats in the range 0 to 1
    and returns a sequence of points defining a Bezier curve from the given control points.

    Parameters
    ----------
    xys : list of tuples
        A sequence of 2-tuples (Bezier control points).

    Returns
    -------
    function
        A function that takes a sequence of floats and returns a sequence of points that define a Bezier curve.
    """
    n = len(xys)
    combinations = pascal_row(n - 1)

    def bezier(ts: List[float]) -> List[Tuple[float, float]]:
        result = []
        for t in ts:
            tpowers = (t**i for i in range(n))
            upowers = reversed([(1 - t)**i for i in range(n)])
            coefs = [c * a * b for c, a, b in zip(combinations, tpowers, upowers)]
            result.append(
                list(sum(coef * p for coef, p in zip(coefs, ps)) for ps in zip(*xys))
            )
        return result

    return bezier

def mouse_bez(init_pos: Tuple[int, int], fin_pos: Tuple[int, int], deviation: int, speed: int) -> List[Tuple[float, float]]:
    """
    Generates Bezier curve points for mouse movement.

    Parameters
    ----------
    init_pos : tuple
        Initial position as (x, y) coordinates.
    fin_pos : tuple
        Final position as (x, y) coordinates.
    deviation : int
        Maximum deviation for the control points.
    speed : int
        Speed multiplier for the movement.

    Returns
    -------
    list
        List of points defining the Bezier curve.
    """
    ts = [t / (speed * 100.0) for t in range(speed * 101)]
    control_1 = (
        init_pos[0] + choice((-1, 1)) * abs(ceil(fin_pos[0]) - ceil(init_pos[0])) * 0.01 * randint(deviation // 2, deviation),
        init_pos[1] + choice((-1, 1)) * abs(ceil(fin_pos[1]) - ceil(init_pos[1])) * 0.01 * randint(deviation // 2, deviation)
    )
    control_2 = (
        init_pos[0] + choice((-1, 1)) * abs(ceil(fin_pos[0]) - ceil(init_pos[0])) * 0.01 * randint(deviation // 2, deviation),
        init_pos[1] + choice((-1, 1)) * abs(ceil(fin_pos[1]) - ceil(init_pos[1])) * 0.01 * randint(deviation // 2, deviation)
    )

    xys = [init_pos, control_1, control_2, fin_pos]
    bezier = make_bezier(xys)
    points = bezier(ts)

    return points

def connected_bez(coord_list: List[Tuple[int, int]], deviation: int, speed: int) -> List[Union[Tuple[int, int], str]]:
    """
    Connects all coordinates in coord_list with a Bezier curve
    and returns the coordinates along the curve.

    Parameters
    ----------
    coord_list : list of tuples
        List of (x, y) coordinates to connect.
    deviation : int
        Maximum deviation for the control points.
    speed : int
        Speed multiplier for the movement.

    Returns
    -------
    list
        List of coordinates along the Bezier curve or 'empty' if coord_list is empty.
    """
    if not coord_list:
        return 'empty'
    points = []
    for start, end in zip(coord_list, coord_list[1:]):
        points.extend(mouse_bez(start, end, deviation, speed))
    return points

def move(points: List[Tuple[float, float]]) -> None:
    """
    Moves the mouse cursor to each point in the provided list.

    Parameters
    ----------
    points : list of tuples
        List of (x, y) points to move the mouse to.
    """
    for point in points:
        pyautogui.moveTo(point[0], point[1])
        sleep(0.01)  # Small sleep to avoid overwhelming the system


# Constants for mouse events
MOUSEEVENTF_MOVE = 0x0001       # Move the mouse
MOUSEEVENTF_ABSOLUTE = 0x8000   # Absolute move
MOUSEEVENTF_LEFTDOWN = 0x0002   # Left mouse button down
MOUSEEVENTF_LEFTUP = 0x0004     # Left mouse button up
MOUSEEVENTF_RIGHTDOWN = 0x0008  # Right mouse button down
MOUSEEVENTF_RIGHTUP = 0x0010    # Right mouse button up
screen_width = ctypes.windll.user32.GetSystemMetrics(0)
screen_height = ctypes.windll.user32.GetSystemMetrics(1)


def windows_get_cursor_pos():
    """Get the position of the mouse cursor on the screen.

    Returns:
    tuple: A tuple containing the x and y coordinates of the mouse cursor.
    """
    x = ctypes.c_ulong()
    y = ctypes.c_ulong()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(x), ctypes.byref(y))
    return x.value, y.value


def windows_set_cursor_pos(x, y):
    """Set the position of the mouse cursor on the screen.

    Parameters:
    x (int): The x-coordinate of the position to set the cursor to.
    y (int): The y-coordinate of the position to set the cursor to.
    """
    ctypes.windll.user32.SetCursorPos(x, y)


def windows_mouse_click(x, y):
    """Click the mouse at the specified coordinates on the screen.

    Parameters:
    x (int): The x-coordinate of the position to click the mouse at.
    y (int): The y-coordinate of the position to click the mouse at.

    Notes:
    The coordinates are specified in absolute coordinates, which are
    coordinates that are relative to the top-left corner of the
    screen. The coordinates are in pixels.

    The absolute coordinates are converted to the 0-65535 range
    that is required by the Windows API.

    """
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def windows_move_mouse_absolute(x, y):
    # Convert x, y to absolute coordinates (0-65535 range)
    """
    Move the mouse to a specific absolute position on the screen.

    Parameters:
    x (int): The x-coordinate of the position to move to.
    y (int): The y-coordinate of the position to move to.

    Notes:
    The position is specified in absolute coordinates, which are
    coordinates that are relative to the top-left corner of the
    screen. The coordinates are in pixels.

    The absolute coordinates are converted to the 0-65535 range
    that is required by the Windows API.

    """
    abs_x = int(x * 65535 / screen_width)
    abs_y = int(y * 65535 / screen_height)

    # Move the mouse to the absolute position
    ctypes.windll.user32.mouse_event(
        MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, abs_x, abs_y, 0, 0)


class WindowsMouseBez:
    def __init__(self):
        self.init = windows_get_cursor_pos()

    def move(self, x, y):
        speed = randint(1, 2)
        deviation = randint(5, 15)
        bez = mouse_bez(self.init, (x, y), speed=speed, deviation=10)
        for coord in bez:
            windows_move_mouse_absolute(coord[0], coord[1])
            self.init = windows_get_cursor_pos()

    def click(self):
        windows_mouse_click(self.init[0], self.init[1])

from webbrowser import Chrome
import win32gui
import time
from PIL import Image, ImageDraw,ImageGrab

def GetGameImage(imageFolder, chromeTabTitle):
    toplist, winlist = [], []
    def enum_cb(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(enum_cb, toplist)

    chrome = [(hwnd, title) for hwnd, title in winlist if chromeTabTitle in title.lower()]
    chrome = chrome[0]
    hwnd = chrome[0]
    full_screen_bbox = (0, 0, 2560, 1440)

    win32gui.SetForegroundWindow(hwnd)
    time.sleep(1)
    bbox = win32gui.GetWindowRect(hwnd)
    img = ImageGrab.grab(full_screen_bbox)

    from PuzzleDetection import SearchForPuzzlePieces
    SearchForPuzzlePieces(imageFolder, img)
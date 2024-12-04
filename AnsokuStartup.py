from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from colorama import init, Fore, Back, Style
from GetImage import GetGameImage
from selenium import webdriver
from webbrowser import Chrome
import pyautogui
import win32gui
import time
import os

def StartAI(puzzlePieceFolder, chromeTabTitle, hwnd, gui_Instance):
    toplist, winlist = [], []
    def enum_cb(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(enum_cb, toplist)

    chrome = [(hwnd, title) for hwnd, title in winlist if chromeTabTitle in title.lower()]
    if not chrome:
        StartupAnsokuWindow(puzzlePieceFolder, chromeTabTitle, hwnd, gui_Instance)
    else:
        GetGameImage(puzzlePieceFolder, chromeTabTitle, hwnd, gui_Instance)


def StartupAnsokuWindow(puzzlePieceFolder, chromeTabTitle, hwnd, gui_Instance):
    global driver
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option("useAutomationExtension", False) 
    options.add_experimental_option("excludeSwitches",["enable-automation"])
    options.add_argument(r"user-data-dir=C:/Users/{Username}/AppData/Local/Google/Chrome/User Data")

    # Initialize the Chrome driver
    service = webdriver.ChromeService(executable_path=os.getcwd() + "/Driver/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    # Navigate to the desired URL
    driver.get("https://ansoku.app/game.php")

    pyautogui.press('f11')

    EnterPlayState(puzzlePieceFolder, chromeTabTitle, hwnd, gui_Instance)

def EnterPlayState(puzzlePieceFolder, chromeTabTitle, hwnd, gui_Instance):
    time.sleep(6)

    pyautogui.click(1280,1240)

    time.sleep(0.3)

    pyautogui.click(1280,820)

    time.sleep(5)

    GetGameImage(puzzlePieceFolder, chromeTabTitle, hwnd, gui_Instance)
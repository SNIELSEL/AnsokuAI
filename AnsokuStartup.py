from turtle import done
from selenium.webdriver.common.action_chains import ActionChains
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_checker import check_env
from selenium.webdriver.common.keys import Keys
from colorama import init, Fore, Back, Style
from stable_baselines3 import PPO
from stable_baselines3 import A2C
from MachineLearningEnvoirement import AnsokuEnv
from colorama import Fore
from tensorboard import program
from selenium import webdriver
from webbrowser import Chrome
from GetImage import GetGameImage
import gymnasium as gym
import pyautogui
import win32gui
import os
import time

model_name = "PPO"
models_dir = f"Models/{model_name}"
logdir = "Logs/"
trainingSteps= 50000

def StartAI(puzzlePieceFolder, chromeTabTitle):
    toplist, winlist = [], []
    def enum_cb(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(enum_cb, toplist)

    chrome = [(hwnd, title) for hwnd, title in winlist if chromeTabTitle in title.lower()]
    if not chrome:
        StartupAnsokuWindow(puzzlePieceFolder, chromeTabTitle)
    else:
        print(Fore.RED + "Already a Window open please close it first and try again")

def launch_tensorboard(logdir):
    tb = program.TensorBoard()
    tb.configure(argv=[None, '--logdir', logdir])
    url = tb.launch()
    print(f"TensorBoard is running at {url}")


def StartupAnsokuWindow(puzzlePieceFolder, chromeTabTitle):
    global driver
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option("useAutomationExtension", False) 
    options.add_experimental_option("excludeSwitches",["enable-automation"])
    options.add_argument(r"user-data-dir=C:/Users/{Username}/AppData/Local/Google/Chrome/User Data")

    service = webdriver.ChromeService(executable_path=os.getcwd() + "/Driver/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://ansoku.app/game.php")

    pyautogui.press('f11')

    EnterPlayState(puzzlePieceFolder, chromeTabTitle)

def EnterPlayState(puzzlePieceFolder, chromeTabTitle):
    time.sleep(9)
    pyautogui.click(1280,1240)
    time.sleep(0.3)
    pyautogui.click(1280,820)
    time.sleep(5)
    pyautogui.click(1280,1240)
    time.sleep(0.5)

    GetGameImage(puzzlePieceFolder, chromeTabTitle)
    
def StartMachineLearningAgent(board_gridcell_values):
    
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    if not os.path.exists(logdir):
        os.makedirs(logdir)

    import threading
    tb_thread = threading.Thread(target=launch_tensorboard, args=(logdir,), daemon=True)
    tb_thread.start()

    env = AnsokuEnv()
    check_env(env)

    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=logdir, device="cpu")
    model.learn(total_timesteps=trainingSteps)
    model.save(f"{models_dir}/AnsokuModel")



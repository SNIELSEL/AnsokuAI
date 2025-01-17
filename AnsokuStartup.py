from multiprocessing import sharedctypes
from turtle import done
from selenium.webdriver.common.action_chains import ActionChains
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_checker import check_env
from selenium.webdriver.common.keys import Keys
from colorama import init, Fore, Back, Style
from stable_baselines3 import PPO
from stable_baselines3 import A2C
from MachineLearningEnvoirement import AnsokuEnv
from selenium import webdriver
from webbrowser import Chrome
from GetImage import GetGameImage
import SharedData
import gymnasium as gym
import pyautogui
import win32gui
from CommonImports import *

model_name = SharedData.model_name
models_dir = SharedData.models_dir
logdir = SharedData.logdir
trainingSteps = SharedData.trainingSteps

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
    
    from PuzzleDetection import SearchForPuzzlePieces, SearchForPuzzleOnGrid
    SearchForPuzzlePieces(puzzlePieceFolder, SharedData.screen_img)

    import SharedData as newData
    original_img_grid = SearchForPuzzleOnGrid(newData.screen_img, newData.screen_img_opencv)

    newData.id.display_image(original_img_grid, (457, 32, 823, 690))

    from AnsokuStartup import StartMachineLearningAgent
    StartMachineLearningAgent()
    
def StartMachineLearningAgent():
    
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    if not os.path.exists(logdir):
        os.makedirs(logdir)

    env = AnsokuEnv()
    check_env(env)

    if SharedData.using_PPO_model:

        SharedData.model_name = "PPO"

        model = PPO("MlpPolicy", env, device="cpu",verbose=1,learning_rate=3e-4,n_steps=4096,batch_size=128,n_epochs=8,gamma=0.99,
        gae_lambda=0.95, clip_range=0.2, ent_coef=0.05, tensorboard_log=logdir)

    else:

        SharedData.model_name = "A2C"

        model = A2C("MlpPolicy", env, device="cpu", verbose=1, learning_rate=7e-4, n_steps=10, gamma=0.995, gae_lambda=1.0, ent_coef=0.05,
        max_grad_norm=0.5,use_rms_prop=True, rms_prop_eps=1e-5, normalize_advantage=True, tensorboard_log=logdir)

    print(SharedData.model_name)

    total_timesteps = SharedData.trainingSteps
    checkpoint_interval = int(total_timesteps / SharedData.trainingCheckpoints)

    for step in range(0, total_timesteps, checkpoint_interval):
        model.learn(total_timesteps=checkpoint_interval)
        model.save(f"{models_dir}/AnsokuModel_step_{step + checkpoint_interval}")

    model.save(f"{models_dir}/AnsokuModel_final")
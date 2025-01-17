#important info that sometimes needs to be changed or data that needs to be shared is stored here for easy sharing/changing of data


puzzlePieceFolder = "PuzzlePieces/"
chromeTabTitle = "unity web player"

logdir = "Logs/"
model_name = "A2C"
models_dir = f"Models/{model_name}"

using_PPO_model = True

trainingSteps= int(1e10)
trainingCheckpoints = 100000

maxSteps_distance = 1100

maxSteps_penalty = 2

placedPiece_reward = 10
pickedUPPiece_reward = 5

currentPuzzlePieces = dict(puzzlePiece_left = "Empty", puzzlePiece_middle = "Empty", puzzlePiece_right = "Empty")
board_gridcell_values = None

screen_img = None
screen_img_opencv = None

terminated = False

PuzzleImage1 = None
PuzzleImage2 = None
PuzzleImage3 = None
image_variants = None

hwnd = None
id = None
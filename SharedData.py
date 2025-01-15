#important info that sometimes needs to be changed or data that needs to be shared is stored here for easy sharing/changing of data


puzzlePieceFolder = "PuzzlePieces/"
chromeTabTitle = "unity web player"

logdir = "Logs/"
model_name = "PPO"
models_dir = f"Models/{model_name}"

trainingSteps= int(1e10)

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
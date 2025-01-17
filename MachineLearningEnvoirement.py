from calendar import TUESDAY
from math import fabs
from time import sleep
import time
from cv2 import fastAtan2
import gymnasium as gym
from gymnasium import spaces
import ctypes
import win32api
import SharedData
import pyautogui
from CommonImports import *

cursorSpeed = 8

init(strip=False, convert=False, autoreset=True)

class AnsokuEnv(gym.Env):
    def getPuzzleNames(self):
        self.image_folder = "./PuzzlePieces"

        self.piece_names = ["Empty"]
        for root, _, files in os.walk(self.image_folder):
            for file in files:
                if file.endswith(".png"):
                    name, _ = os.path.splitext(file)
                    if name not in self.piece_names:
                        self.piece_names.append(name)

        self.piece_name_to_id = {name: idx for idx, name in enumerate(self.piece_names)}
        self.num_pieces = len(self.piece_names)

    def convertBool(self, convertBool):
        if convertBool:
            convertBool = 1
        else:
            convertBool = 0
        return convertBool

    def __init__(self):
        super().__init__()

        self.leftdown = 0x0002
        self.leftup = 0x0004

        from SharedData import board_gridcell_values
        self.board_data = board_gridcell_values
        
        self.action_space = spaces.Discrete(10)
        
        self.getPuzzleNames()
        self.placedPieceTotal = 0
        self.failedPlacements = 0
        self.playedGames = 0

        self.observation_space = spaces.MultiDiscrete(
            [2] * len(self.board_data) + [2560, 1440] +              
            [1135 + 1, 1130 + 1] +       
            [1285 + 1, 1130 + 1] +      
            [1430 + 1, 1130 + 1] +       
            [int(1e3)] +
            [int(1e3)] +
            [int(1e3)] +
            [2, 2, 2, 2, 2, 2, 2] +
            [int(1e4)] +
            [int(1e4)] +
            [int(1e4)] +
            [int(1e5)] +
            [self.num_pieces] * 3 
        )

        
        encoded_board = [
        0 if value == 'empty' else 1
        for value in self.board_data.values()
        ]

        self.target_centers = {
        'left': (1135, 1130),
        'mid': (1285, 1130),
        'right': (1430, 1130)}

        self.leftPuzzle_distance = 0
        self.middlePuzzle_distance = 0
        self.rightPuzzle_distance = 0

        self.hold_left = False
        self.hold_mid = False
        self.hold_right = False

        self.placed_left = False
        self.placed_mid = False
        self.placed_right = False
        self.holdingPiece_time = 0
        self.holdingPiece_bool = False
        self.totalDistance_moved = 0

    def get_mouse_position(self):
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def move_relative(self, dx, dy):

        current_x, current_y = self.get_mouse_position()
        new_x = max(915, min(current_x + dx, 1640))
        new_y = max(70, min(current_y + dy, 1370))
        ctypes.windll.user32.SetCursorPos(new_x, new_y + dy)

    def step(self, action):
        mouseX, mouseY = self.get_mouse_position()
        actionReward = 0

        if self.holdingPiece_time <= 10:
            self.holdingPiece_time = time.time()

        #compares the new board with the old for differences if there is a difference it means a puzzle piece has been placed
        def CompareBoardPieces():

            self.old_board_data = self.board_data

            from GetImage import GetGameImage
            GetGameImage(SharedData.puzzlePieceFolder,SharedData.chromeTabTitle)

            from PuzzleDetection import SearchForPuzzleOnGrid
            import SharedData as newSharedData
            SearchForPuzzleOnGrid(newSharedData.screen_img,newSharedData.screen_img_opencv)

            from SharedData import board_gridcell_values as new_boardData

            if self.old_board_data == new_boardData:
                return False
            else:
                self.old_board_data = new_boardData
                return True
            
        def VerifyImagePlaced(puzzleNumber):

            puzzle_variants = []

            from GetImage import GetGameImage
            GetGameImage(SharedData.puzzlePieceFolder,SharedData.chromeTabTitle)

            import SharedData as verificationData

            puzzlePiece_img = cv.imread("PuzzlePieces/GameOver.png", cv.IMREAD_REDUCED_COLOR_2)

            img_check = np.array(verificationData.screen_img)
            img_check = cv.cvtColor(img_check, cv.COLOR_RGB2BGR)

            original_height, original_width = puzzlePiece_img.shape[:2]
            new_width, new_height = original_width // 2, original_height // 2
            puzzlePiece_img = cv.resize(puzzlePiece_img, (new_width, new_height))

            original_height, original_width = img_check.shape[:2]
            new_width, new_height = original_width // 2, original_height // 2
            img_check = cv.resize(img_check, (new_width, new_height))

            result = cv.matchTemplate(img_check, puzzlePiece_img, cv.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)

            #print(Fore.GREEN + "Match value = " + str(max_val) + Fore.WHITE)

            #checks if gameover screen is detected
            matchingImageThreshold = 0.76
            if(max_val >= matchingImageThreshold):
                actionReward -= 10
                verificationData.terminated = True
            else:
                verificationData.terminated = False

            #image info for debugging
            #cv.imshow("fullscreen", img_check)
            #cv.imshow("Gameover", puzzlePiece_img)
            #cv.waitKey()

            img = verificationData.screen_img
            for i, rects in enumerate(verificationData.image_variants, 1):
                variant_img = img.copy()
                draw = ImageDraw.Draw(variant_img)
    
                for rect in rects:
                    draw.rectangle(rect, fill="black")
    
                puzzle_variants.append(variant_img)

            for variant_img in puzzle_variants:

                variant_img_cv = np.array(variant_img)
                variant_img_cv = cv.cvtColor(variant_img_cv, cv.COLOR_RGB2BGR)

                original_height, original_width = variant_img_cv.shape[:2]
                new_width, new_height = original_width // 2, original_height // 2
                variantResized_img = cv.resize(variant_img_cv, (new_width, new_height))

                if(variant_img == puzzle_variants[0]):
                    result = cv.matchTemplate(variantResized_img, verificationData.PuzzleImage1, cv.TM_CCOEFF_NORMED)

                    #gives values of whitest and blackest place and their location of the black and white image generated by the matchTemplate
                    puzzle1_min_val, puzzle1_max_val, puzzle1_min_loc, puzzle1_max_loc = cv.minMaxLoc(result)
                    #print(Fore.GREEN +str(puzzle1_max_val) + Fore.WHITE)

                elif(variant_img == puzzle_variants[1]):
                    result = cv.matchTemplate(variantResized_img, verificationData.PuzzleImage2, cv.TM_CCOEFF_NORMED)

                    #gives values of whitest and blackest place and their location of the black and white image generated by the matchTemplate
                    puzzle2_min_val, puzzle2_max_val, puzzle2_min_loc, puzzle2_max_loc = cv.minMaxLoc(result)
                    #print(Fore.GREEN +str(puzzle2_max_val) + Fore.WHITE)

                elif(variant_img == puzzle_variants[2]):
                    result = cv.matchTemplate(variantResized_img, verificationData.PuzzleImage3, cv.TM_CCOEFF_NORMED)

                    #gives values of whitest and blackest place and their location of the black and white image generated by the matchTemplate
                    puzzle3_min_val, puzzle3_max_val, puzzle3_min_loc, puzzle3_max_loc = cv.minMaxLoc(result)
                    #print(Fore.GREEN +str(puzzle3_max_val) + Fore.WHITE)

            matchingImageThreshold = 0.66
            #first checks other pieces to make sure its set correct the returns the info of requested puzzle
            if puzzleNumber == 1:

                if puzzle2_max_val >= matchingImageThreshold:
                    if self.placed_mid == True:
                        self.placed_mid = False
                else:
                    if self.placed_mid == False:
                        self.placed_mid = True

                if puzzle3_max_val >= matchingImageThreshold:
                    if self.placed_right == True:
                        self.placed_right = False
                else:
                    if self.placed_right == False:
                        self.placed_right = True

                if puzzle1_max_val >= matchingImageThreshold:
                    if self.placed_left == True:
                        return False
                else:
                    if self.placed_left == False:
                        return True

            elif puzzleNumber == 2:

                if puzzle1_max_val >= matchingImageThreshold:
                    if self.placed_left == True:
                        self.placed_left = False
                else:
                    if self.placed_left == False:
                        self.placed_left = True

                if puzzle3_max_val >= matchingImageThreshold:
                    if self.placed_right == True:
                        self.placed_right = False
                else:
                    if self.placed_right == False:
                        self.placed_right = True

                if puzzle2_max_val >= matchingImageThreshold:
                    if self.placed_mid == True:
                        return False
                else:
                    if self.placed_mid == False:
                        return True

            elif puzzleNumber == 3:

                if puzzle1_max_val >= matchingImageThreshold:
                    if self.placed_left == True:
                        self.placed_left = False
                else:
                    if self.placed_left == False:
                        self.placed_left = True

                if puzzle2_max_val >= matchingImageThreshold:
                    if self.placed_mid == True:
                        self.placed_mid = False
                else:
                    if self.placed_mid == False:
                        self.placed_mid = True

                if puzzle3_max_val >= matchingImageThreshold:
                    if self.placed_right == True:
                        return False
                else:
                    if self.placed_right == False:
                        return True

        #chooses its action from one in this switch case
        match action:
            case 0:
                #Move Up
                self.totalDistance_moved += cursorSpeed

                if self.totalDistance_moved >= SharedData.maxSteps_distance:
                    actionReward -= SharedData.maxSteps_penalty
                    self.totalDistance_moved = 0
                else:
                    self.move_relative(0, -cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 2
        
            case 1:
                #Down

                self.totalDistance_moved += cursorSpeed

                if self.totalDistance_moved >= SharedData.maxSteps_distance:
                    actionReward -= SharedData.maxSteps_penalty
                    self.totalDistance_moved = 0
                else:
                    self.move_relative(0, cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 2

            case 2:
                #Left
                self.totalDistance_moved += cursorSpeed

                if self.totalDistance_moved >= SharedData.maxSteps_distance:
                    actionReward -= SharedData.maxSteps_penalty
                    self.totalDistance_moved = 0
                else:
                    self.move_relative(-cursorSpeed, 0)

                if mouseY <= 420:
                    actionReward -= 2

            case 3:
                #Right
                self.totalDistance_moved += cursorSpeed

                if self.totalDistance_moved >= SharedData.maxSteps_distance:
                    actionReward -= SharedData.maxSteps_penalty
                    self.totalDistance_moved = 0
                else:
                    self.move_relative(cursorSpeed, 0)

                if mouseY <= 420:
                    actionReward -= 2

            case 4:
                #UpLeft
                self.totalDistance_moved += cursorSpeed

                if self.totalDistance_moved >= SharedData.maxSteps_distance:
                    actionReward -= SharedData.maxSteps_penalty
                    self.totalDistance_moved = 0
                else:
                    self.move_relative(-cursorSpeed, -cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 2

            case 5:
                #UpRight
                self.totalDistance_moved += cursorSpeed

                if self.totalDistance_moved >= SharedData.maxSteps_distance:
                    actionReward -= SharedData.maxSteps_penalty
                    self.totalDistance_moved = 0
                else:
                    self.move_relative(cursorSpeed, -cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 2

            case 6:
                #DownLeft
                self.totalDistance_moved += cursorSpeed

                if self.totalDistance_moved >= SharedData.maxSteps_distance:
                    actionReward -= SharedData.maxSteps_penalty
                    self.totalDistance_moved = 0
                else:
                    self.move_relative(-cursorSpeed, cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 2

            case 7:
                #DownRight
                self.totalDistance_moved += cursorSpeed

                if self.totalDistance_moved >= SharedData.maxSteps_distance:
                    actionReward -= SharedData.maxSteps_penalty
                    self.totalDistance_moved = 0
                else:
                    self.move_relative(cursorSpeed, cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 2

            case 8:
                #LeftMouseDown
                #checks if clicking on the options button or rotate/undo and if then give negative reward and else releases mouse
                if (930 <= mouseX <= 1100 and 65 <= mouseY <= 420) or (1490 <= mouseX <= 1640 and 260 <= mouseY <= 440):
                    pass
                else:
                    if not self.hold_left and not self.hold_mid and not self.hold_right:
                        #checks if inside the the square that contains the 3 placeable puzzle pieces
                        if 1070 <= mouseX <= 1500 and 1042 <= mouseY <= 1215:
                            actionReward += 1
                            #checks if inside a rectangle of the left puzzle piece and if it is it hold the puzzle piece
                            if 1105 <= mouseX <= 1165 and 1100 <= mouseY <= 1160 and not self.placed_left:
                                actionReward += SharedData.pickedUPPiece_reward

                                self.hold_left = True;
                                self.holdingPiece_bool = True

                                ctypes.windll.user32.mouse_event(self.leftdown, 0, 0, 0, 0)
                                self.totalDistance_moved = 0
                            #checks if inside a rectangle of the middle puzzle piece and if it is it hold the puzzle piece
                            elif 1255 <= mouseX <= 1315 and 1100 <= mouseY <= 1160 and not self.placed_mid:
                                actionReward += SharedData.pickedUPPiece_reward

                                self.hold_mid = True;
                                self.holdingPiece_bool = True

                                ctypes.windll.user32.mouse_event(self.leftdown, 0, 0, 0, 0)
                                self.totalDistance_moved = 0
                            #checks if inside a rectangle of the right puzzle piece and if it is it hold the puzzle piece
                            elif 1400 <= mouseX <= 1460 and 1100 <= mouseY <= 1160 and not self.placed_right:
                                actionReward += SharedData.pickedUPPiece_reward

                                self.hold_right = True;
                                self.holdingPiece_bool = True

                                ctypes.windll.user32.mouse_event(self.leftdown, 0, 0, 0, 0)
                                self.totalDistance_moved = 0
                            else:
                                pass
                        else:
                            #not clicking on the pieces board
                            pass
                    else:
                        pass
        
            case 9:
                #LeftMouseUp/ReleaseMouse
                mouseX, mouseY = self.get_mouse_position()
                #checks if clicking on the options button or rotate/undo and if then give negative reward and else releases mouse
                if (930 <= mouseX <= 1100 and 65 <= mouseY <= 420) or (1490 <= mouseX <= 1640 and 260 <= mouseY <= 440):
                    pass
                else:
                    if self.hold_left or self.hold_mid or self.hold_right:
                        actionReward += 1          
                        #checks what piece its holding then checks the difference with the old 
                        #board if there is a difference then the piece will be placed
                        if self.hold_left and not self.placed_left and mouseY <= 1042:

                            actionReward += 1
                            if CompareBoardPieces() == True:

                                actionReward += 1

                                ctypes.windll.user32.mouse_event(self.leftup, 0, 0, 0, 0)

                                self.hold_left = False

                                time.sleep(1)

                                self.placed_left = VerifyImagePlaced(1)

                                #succecfully placed left puzzle
                                if self.placed_left == True:

                                    self.holdingPiece_bool = False

                                    self.totalDistance_moved = 0
                                    self.failedPlacements = 0
                                    self.placedPieceTotal += 1

                                    self.holdingPiece_time = time.time()

                                    actionReward += SharedData.placedPiece_reward
                                else:
                                    #failed to place and puzzle was detected back on the board
                                    self.failedPlacements += 1
                                    actionReward -= self.failedPlacements * 2
                            else:
                                self.hold_left = VerifyImagePlaced(1)
                                self.failedPlacements += 1
                                actionReward -= self.failedPlacements * 2

                        #midle puzzle
                        elif self.hold_mid and not self.placed_mid and mouseY <= 1042:
                            actionReward += 1
                            if CompareBoardPieces() == True:

                                actionReward += 1

                                ctypes.windll.user32.mouse_event(self.leftup, 0, 0, 0, 0)
                                self.hold_mid = False
                                time.sleep(1)

                                self.placed_mid = VerifyImagePlaced(2)

                                #succecfully placed middle puzzle
                                if self.placed_mid == True:

                                    self.holdingPiece_bool = False

                                    self.totalDistance_moved = 0
                                    self.failedPlacements = 0
                                    self.placedPieceTotal += 1

                                    self.holdingPiece_time = time.time()

                                    actionReward += SharedData.placedPiece_reward
                                else:
                                    #failed to place and puzzle was detected back on the board
                                    self.failedPlacements += 1
                                    actionReward -= self.failedPlacements * 2
                            else:
                                self.hold_mid = VerifyImagePlaced(2)
                                self.failedPlacements += 1
                                actionReward -= self.failedPlacements * 2

                        #right puzzle
                        elif self.hold_right and not self.placed_right and mouseY <= 1042:
                            actionReward += 1
                            if CompareBoardPieces() == True:

                                actionReward += 1

                                ctypes.windll.user32.mouse_event(self.leftup, 0, 0, 0, 0)
                                self.hold_right = False
                                time.sleep(1)

                                self.placed_right = VerifyImagePlaced(3)

                                #succecfully placed right puzzle
                                if self.placed_right == True:

                                    self.holdingPiece_bool = False
                                        
                                    self.totalDistance_moved = 0
                                    self.failedPlacements = 0
                                    self.placedPieceTotal += 1
                                        
                                    self.holdingPiece_time = time.time()
                                        
                                    actionReward += SharedData.placedPiece_reward
                                else:
                                    self.failedPlacements += 1
                                    actionReward -= self.failedPlacements * 2
                            else:
                                self.hold_right = VerifyImagePlaced(3)
                                self.failedPlacements += 1
                                actionReward -= self.failedPlacements * 2

                    else:
                       pass

        if 918 <= mouseX <= 1637 and  73 <= mouseY <= 1367:
            pass
        else:
            actionReward -= 5

        #debu info
        #print("playedGames status is " + str(self.playedGames) + " and a mult of " + str(self.gameCostMult))
        #print("placedPieces status is " + str(self.placedPieceTotal))
        #print("Mouse x and y status status is " + str(mouseX) + "x" + str(mouseY))
        #print("Holding status \n"+ "left = " + str(self. hold_left) + " mid = " + str(self. hold_mid)+ " right = " + str(self. hold_right))
        #print("Placed status \n"+ "left = " + str(self. placed_left) + " mid = " + str(self. placed_mid)+ " right = " + str(self. placed_right))
        #print("distanceMoved status is " + str(self. totalDistance_moved))


        proximity_reward = self.calculate_proximity_reward(mouseX, mouseY)
        actionReward += proximity_reward
        actionReward += self.placedPieceTotal
        actionReward -= self.playedGames

        #placed all 3 pieces so get 3 new ones scan them and begin again
        if(self.placed_left and self.placed_mid and self.placed_right):
            actionReward += 50
            time.sleep(1)
            pyautogui.click(1280,1250)
            self.placed_left = False
            self.placed_mid = False
            self.placed_right = False
            time.sleep(3)
            pyautogui.click(1280,1240)

            from GetImage import GetGameImage
            GetGameImage(SharedData.puzzlePieceFolder,SharedData.chromeTabTitle)

            from PuzzleDetection import SearchForPuzzlePieces, SearchForPuzzleOnGrid
            SearchForPuzzlePieces(SharedData.puzzlePieceFolder, SharedData.screen_img)

            self.getPuzzleNames()

            import SharedData as newData
            original_img_grid = SearchForPuzzleOnGrid(newData.screen_img, newData.screen_img_opencv)

            newData.id.display_image(original_img_grid, (457, 32, 823, 690))

            self.holdingPiece_time = time.time()

        currentTime = time.time()
        timeSinceLastAction = currentTime - self.holdingPiece_time

        if timeSinceLastAction >= 240:
            actionReward -= 15
            SharedData.terminated = True

        terminated = SharedData.terminated
        truncated = False
        observation = self.get_observation()
        info = self.get_info()

        #print(actionReward)
        return observation, actionReward, terminated, truncated, info

    def calculate_proximity_reward(self, mouseX, mouseY):
        proximity_reward = 0
        self.leftPuzzle_distance = 0
        self.middlePuzzle_distance = 0
        self.rightPuzzle_distance = 0

        for region, center in self.target_centers.items():
            if not getattr(self, f'placed_{region}'):
                center_x, center_y = center
                distance = np.sqrt((mouseX - center_x) ** 2 + (mouseY - center_y) ** 2)

                x_min, x_max = 918, 1637
                y_min, y_max = 73, 1367

                width  = x_max - x_min 
                height = y_max - y_min
            
                max_distance = np.sqrt(width**2 + height**2)

                normalized_distance = 1 - (distance / max_distance)
            
                reward = normalized_distance * 2
            
                proximity_reward += reward

                if region == "left":
                    self.leftPuzzle_distance += reward
                elif region == "mid":
                    self.middlePuzzle_distance += reward
                elif region == "right":
                    self.rightPuzzle_distance += reward

        return proximity_reward


    #Get all the datat for the ai so it can use it to check what actions/values
    #where used after an action so it can use it to guess what actions at what specific time give it positive reward
    def get_observation(self):
        isholding = self.convertBool(self.holdingPiece_bool)

        hold_left = self.convertBool(self.hold_left)
        hold_mid = self.convertBool(self.hold_mid)
        hold_right = self.convertBool(self.hold_right)

        placed_left = self.convertBool(self.placed_left)
        placed_mid = self.convertBool(self.placed_mid)
        placed_right = self.convertBool(self.placed_right)

        from SharedData import board_gridcell_values
        self.board_data = board_gridcell_values

        board_encoded = [
            0 if value == 'empty' else 1
            for value in self.board_data.values()
        ]
        mouse_x, mouse_y = self.get_mouse_position()
        
        from SharedData import currentPuzzlePieces
        left_piece_name = SharedData.currentPuzzlePieces.get("puzzlePiece_left", "Empty")
        middle_piece_name = SharedData.currentPuzzlePieces.get("puzzlePiece_middle", "Empty")
        right_piece_name = SharedData.currentPuzzlePieces.get("puzzlePiece_right", "Empty")
        
        left_piece_id = self.piece_name_to_id.get(left_piece_name, 0)
        middle_piece_id = self.piece_name_to_id.get(middle_piece_name, 0)
        right_piece_id = self.piece_name_to_id.get(right_piece_name, 0)

        if not self.placed_left:
            puzzle1_posX = 1135
            puzzle1_posY = 1130
        else:
            puzzle1_posX = 0
            puzzle1_posY = 0

        if not self.placed_mid:
            puzzle2_posX = 1285
            puzzle2_posY = 1130
        else:
            puzzle2_posX = 0
            puzzle2_posY = 0

        if not self.placed_right:
            puzzle3_posX = 1430
            puzzle3_posY = 1130
        else:
            puzzle3_posX = 0
            puzzle3_posY = 0

        observation = board_encoded + [mouse_x, mouse_y] + [puzzle1_posX, puzzle1_posY] + [puzzle2_posX, puzzle2_posY] + [puzzle3_posX, 
        puzzle3_posY] +[self.leftPuzzle_distance,self.middlePuzzle_distance,self.rightPuzzle_distance]+ [isholding, hold_left, hold_mid, hold_right, placed_left, placed_mid, placed_right,
        self.playedGames, self.placedPieceTotal, self.failedPlacements, self.totalDistance_moved, 
        left_piece_id, middle_piece_id, right_piece_id]

        print(observation)
        return np.array(observation, dtype=np.int32)


    #gets extra info from an array to check what grid cell is empty or has a puzzle piece
    def get_info(self):
        num_puzzle = sum(1 for value in self.board_data.values() if value == 'puzzle')
        num_empty = sum(1 for value in self.board_data.values() if value == 'empty')
        return {
            "num_puzzle": num_puzzle,
            "num_empty": num_empty
        }

    #resets values after 1 training session
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        terminated = SharedData.terminated

        self.holdingPiece_time = 0
        self.holdingPiece_bool = False

        observation = self.get_observation()
        info = self.get_info()

        self.hold_left = False
        self.hold_mid = False
        self.hold_right = False

        if terminated == True:
            #click home twice for if the first doesnt get registerd and also does the some for the others for the same reason
            pyautogui.click(1000,125)
            pyautogui.click(1000,125)
            time.sleep(4)
            #click new game
            pyautogui.click(1285,920)
            pyautogui.click(1285,920)
            time.sleep(1)
            #click new game backup for if first fails (happens often)
            pyautogui.click(1285,920)
            pyautogui.click(1285,920)
            time.sleep(1)
            #click confirm
            pyautogui.click(1455,1135)
            pyautogui.click(1455,1135)
            time.sleep(1)
            #click confirm backup for if the first one doesnt register
            pyautogui.click(1455,1135)
            pyautogui.click(1455,1135)
            time.sleep(7)
            #mouse to button
            pyautogui.click(1280,1240)
            pyautogui.click(1280,1240)

            self.placed_left = False
            self.placed_mid = False
            self.placed_right = False

            self.leftPuzzle_distance = 0
            self.middlePuzzle_distance = 0
            self.rightPuzzle_distance = 0
            self.failedPlacements = 0
            self.placedPieceTotal = 0

            from GetImage import GetGameImage
            GetGameImage(SharedData.puzzlePieceFolder,SharedData.chromeTabTitle)

            from PuzzleDetection import SearchForPuzzlePieces, SearchForPuzzleOnGrid
            SearchForPuzzlePieces(SharedData.puzzlePieceFolder, SharedData.screen_img)

            import SharedData as newData
            original_img_grid = SearchForPuzzleOnGrid(newData.screen_img, newData.screen_img_opencv)

            newData.id.display_image(original_img_grid, (457, 32, 823, 690))

            self.getPuzzleNames()
            self.holdingPiece_time = time.time()
            self.playedGames += 1

            SharedData.terminated = False

        return observation, info

    def close(self):
        pass


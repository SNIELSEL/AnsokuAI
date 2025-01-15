from calendar import TUESDAY
from math import fabs
from time import sleep
import time
import gymnasium as gym
from gymnasium import spaces
import ctypes
import win32api
import SharedData
import pyautogui
from CommonImports import *

cursorSpeed = 6

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

        self.observation_space = spaces.MultiDiscrete(
            [2] * len(self.board_data) + [2560, 1440] +              
            [1135 + 1, 1130 + 1] +       
            [1336 + 1, 1130 + 1] +      
            [1430 + 1, 1130 + 1] +       
            [2, 2, 2, 2, 2, 2, 2] +       
            [self.num_pieces] * 3 
        )

        
        encoded_board = [
        0 if value == 'empty' else 1
        for value in self.board_data.values()
        ]

        self.target_centers = {
        'left': (1135, 1130),
        'mid': (1336, 1130),
        'right': (1430, 1130)}

        self.hold_left = False
        self.hold_mid = False
        self.hold_right = False

        self.placed_left = False
        self.placed_mid = False
        self.placed_right = False

        self.holdingPiece_bool = False
        self.stepsAfterPickup = 0
        self.startup = True
        self.external_rewards = 0

    def get_mouse_position(self):
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def move_relative(self, dx, dy):

        mouseX, mouseY = self.get_mouse_position()
        if (918 <= mouseX <= 1637 and 73 <= mouseY <= 1367):
            current_x, current_y = self.get_mouse_position()
            new_x = max(915, min(current_x + dx, 1640))
            new_y = max(70, min(current_y + dy, 1370))
            ctypes.windll.user32.SetCursorPos(new_x, new_y + dy)
        else:
            self.external_rewards -= 5
            pyautogui.click(1280,1240)


    def step(self, action):
        mouseX, mouseY = self.get_mouse_position()
        actionReward = 0
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

            print(Fore.GREEN + "Match value = " + str(max_val) + Fore.WHITE)

            matchingImageThreshold = 0.76
            if(max_val >= matchingImageThreshold):
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

                if(puzzleNumber == 1 and variant_img == puzzle_variants[0]):
                    result = cv.matchTemplate(variantResized_img, verificationData.PuzzleImage1, cv.TM_CCOEFF_NORMED)

                    #gives values of whitest and blackest place and their location of the black and white image generated by the matchTemplate
                    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
                    print(Fore.GREEN +str(max_val) + Fore.WHITE)

                    matchingImageThreshold = 0.76
                    if(max_val >= matchingImageThreshold):
                        return False
                    else:
                        return True
                elif(puzzleNumber == 2 and variant_img == puzzle_variants[1]):
                    result = cv.matchTemplate(variantResized_img, verificationData.PuzzleImage2, cv.TM_CCOEFF_NORMED)

                    #gives values of whitest and blackest place and their location of the black and white image generated by the matchTemplate
                    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
                    print(Fore.GREEN +str(max_val) + Fore.WHITE)

                    matchingImageThreshold = 0.76
                    if(max_val >= matchingImageThreshold):
                        return False
                    else:
                        return True
                elif(puzzleNumber == 3 and variant_img == puzzle_variants[2]):
                    result = cv.matchTemplate(variantResized_img, verificationData.PuzzleImage3, cv.TM_CCOEFF_NORMED)

                    #gives values of whitest and blackest place and their location of the black and white image generated by the matchTemplate
                    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
                    print(Fore.GREEN +str(max_val) + Fore.WHITE)

                    matchingImageThreshold = 0.76
                    if(max_val >= matchingImageThreshold):
                        return False
                    else:
                        return True

        #chooses its action from one in this switch case
        match action:
            case 0:
                #Up
                self.move_relative(0, -cursorSpeed)
                
                if mouseY <= 420:
                    actionReward -= 1
        
            case 1:
                #Down

                if self.hold_left or self.hold_mid or self.hold_right:
                    if mouseY <= 975:
                        self.move_relative(0, cursorSpeed)
                    else:
                        actionReward -= 1
                else:
                    self.move_relative(0, cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 1

            case 2:
                #Left
                self.move_relative(-cursorSpeed, 0)

                if mouseY <= 420:
                    actionReward -= 1

            case 3:
                #Right
                self.move_relative(cursorSpeed, 0)

                if mouseY <= 420:
                    actionReward -= 1

            case 4:
                #UpLeft
                self.move_relative(-cursorSpeed, -cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 1
        
            case 5:
                #UpRight
                self.move_relative(cursorSpeed, -cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 1
        
            case 6:
                #DownLeft
                if self.hold_left or self.hold_mid or self.hold_right:
                    if mouseY <= 975:
                        self.move_relative(-cursorSpeed, cursorSpeed)
                    else:
                        actionReward -= 1
                else:
                    self.move_relative(-cursorSpeed, cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 1
        
            case 7:
                #DownRight
                if self.hold_left or self.hold_mid or self.hold_right:
                    if mouseY <= 975:
                        self.move_relative(cursorSpeed, cursorSpeed)
                    else:
                        actionReward -= 1
                else:
                    self.move_relative(cursorSpeed, cursorSpeed)

                if mouseY <= 420:
                    actionReward -= 1
        
            case 8:
                #LeftMouseDown
                #checks if clicking on the options button or rotate/undo and if then give negative reward and else releases mouse
                if (930 <= mouseX <= 1100 and 65 <= mouseY <= 420) or (1490 <= mouseX <= 1640 and 260 <= mouseY <= 440):
                    actionReward -= 2
                else:
                    if not self.hold_left and not self.hold_mid and not self.hold_right:
                        #checks if inside the the square that contains the 3 placeable puzzle pieces
                        if 1070 <= mouseX <= 1500 and 1042 <= mouseY <= 1215:
                            #checks if inside a rectangle of the left puzzle piece and if it is it hold the puzzle piece
                            if 1130 <= mouseX <= 1140 and 1120 <= mouseY <= 1140 and not self.placed_left:
                                actionReward += 5

                                self.hold_left = True;
                                self.holdingPiece_bool = True

                                ctypes.windll.user32.mouse_event(self.leftdown, 0, 0, 0, 0)
                            #checks if inside a rectangle of the middle puzzle piece and if it is it hold the puzzle piece
                            elif 1279 <= mouseX <= 1393 and 1122 <= mouseY <= 1138 and not self.placed_mid:
                                actionReward += 5

                                self.hold_mid = True;
                                self.holdingPiece_bool = True

                                ctypes.windll.user32.mouse_event(self.leftdown, 0, 0, 0, 0)
                            #checks if inside a rectangle of the right puzzle piece and if it is it hold the puzzle piece
                            elif 1425 <= mouseX <= 1435 and 1125 <= mouseY <= 1135 and not self.placed_right:
                                actionReward += 5

                                self.hold_right = True;
                                self.holdingPiece_bool = True

                                ctypes.windll.user32.mouse_event(self.leftdown, 0, 0, 0, 0)
                            else:
                                pass
                        else:
                            #not clicking on the pieces board
                            actionReward -= 3

                        print("Mouse x and y status status is " + str(mouseX) + "x" + str(mouseY))
                        print("Holding left status is " + str(self. hold_left))
                        print("Holding mid status is " + str(self. hold_mid))
                        print("Holding right status is " + str(self. hold_right))
                        print("Placed left status is " + str(self. placed_left))
                        print("Placed mid status is " + str(self. placed_mid))
                        print("Placed right status is " + str(self. placed_right))
                    else:
                        actionReward -= 1
        
            case 9:
                #LeftMouseUp/ReleaseMouse
                mouseX, mouseY = self.get_mouse_position()
                #checks if clicking on the options button or rotate/undo and if then give negative reward and else releases mouse
                if (930 <= mouseX <= 1100 and 65 <= mouseY <= 420) or (1490 <= mouseX <= 1640 and 260 <= mouseY <= 440):
                    actionReward -= 0.5
                else:
                    if self.hold_left or self.hold_mid or self.hold_right:
                        #checks if the piece was holding for 1 second or more and if give good reward
                        if self.stepsAfterPickup >=25:
                            self.stepsAfterPickup = 0
           
                            #checks what piece its holding then checks the difference with the old 
                            #board if there is a difference then the piece will be placed
                            if self.hold_left and not self.placed_left:

                                if CompareBoardPieces() == True:

                                    actionReward += 1

                                    ctypes.windll.user32.mouse_event(self.leftup, 0, 0, 0, 0)

                                    self.hold_left = False

                                    time.sleep(1)

                                    self.placed_left = VerifyImagePlaced(1)

                                    actionReward += 10

                                    if self.placed_left == True:
                                        self.holdingPiece_bool = False
                                    else:
                                        actionReward -= 10
                                else:
                                    actionReward -= 1
                            #mid
                            elif self.hold_mid and not self.placed_mid:

                                if CompareBoardPieces() == True:

                                    actionReward += 1

                                    ctypes.windll.user32.mouse_event(self.leftup, 0, 0, 0, 0)
                                    self.hold_mid = False
                                    time.sleep(1)

                                    actionReward += 10

                                    self.placed_mid = VerifyImagePlaced(2)

                                    if self.placed_mid == True:

                                        self.holdingPiece_bool = False
                                    else:
                                        actionReward -= 10
                                else:
                                    actionReward -= 1
                            #right
                            elif self.hold_right and not self.placed_right:

                                if CompareBoardPieces() == True:

                                    actionReward += 1

                                    ctypes.windll.user32.mouse_event(self.leftup, 0, 0, 0, 0)
                                    self.hold_right = False
                                    time.sleep(1)

                                    actionReward += 10

                                    self.placed_right = VerifyImagePlaced(3)

                                    if self.placed_right == True:
                                        self.holdingPiece_bool = False
                                    else:
                                        actionReward -= 10
                                else:
                                    actionReward -= 1

                            #Debug info
                            #print("Holding left status is " + str(self. hold_left))
                            #print("Holding mid status is " + str(self. hold_mid))
                            #print("Holding right status is " + str(self. hold_right))
                            print("Placed left status is " + str(self. placed_left))
                            print("Placed mid status is " + str(self. placed_mid))
                            print("Placed right status is " + str(self. placed_right))
                        else:
                            self.stepsAfterPickup +=1
                    else:
                        pass
        
        proximity_reward = self.calculate_proximity_reward(mouseX, mouseY)
        actionReward += proximity_reward
        actionReward += self.external_rewards

        self.external_rewards = 0

        #placed all 3 pieces so get 3 new ones scan them and begin again
        if(self.placed_left and self.placed_mid and self.placed_right):
            actionReward += 20
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

            import SharedData as newData
            original_img_grid = SearchForPuzzleOnGrid(newData.screen_img, newData.screen_img_opencv)

            newData.id.display_image(original_img_grid, (457, 32, 823, 690))

        else:
            if(self.placed_left):
                actionReward += 0.33
            if(self.placed_mid):
                actionReward += 0.33
            if(self.placed_right):
                actionReward += 0.33

        terminated = SharedData.terminated
        truncated = False
        observation = self.get_observation()
        info = self.get_info()

        print(actionReward)

        return observation, actionReward, terminated, truncated, info

    def calculate_proximity_reward(self, mouseX, mouseY):
        proximity_reward = 0

        for region, center in self.target_centers.items():
            if not getattr(self, f'placed_{region}'):
                center_x, center_y = center
                distance = np.sqrt((mouseX - center_x) ** 2 + (mouseY - center_y) ** 2)
            
                max_distance = np.sqrt(2560**2 + 1440**2)
            
                normalized_distance = distance / max_distance
            
                reward = (1 - normalized_distance) * 1 / 2
            
                proximity_reward += reward

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
            puzzle2_posX = 1336
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

        observation = board_encoded + [mouse_x, mouse_y] + [puzzle1_posX, puzzle1_posY] + [puzzle2_posX, puzzle2_posY] + [puzzle3_posX, puzzle3_posY] + [isholding, hold_left, hold_mid, hold_right, placed_left, placed_mid, placed_right,
        left_piece_id, middle_piece_id, right_piece_id]
        
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
        actionReward = 0

        self.holdingPiece_time = 0
        self.holdingPiece_bool = False
        observation = self.get_observation()
        info = self.get_info()

        self.hold_left = False
        self.hold_mid = False
        self.hold_right = False

        if terminated == True:
            pyautogui.click(1000,125)
            time.sleep(4)
            pyautogui.click(1285,920)
            time.sleep(1)
            pyautogui.click(1455,1135)
            time.sleep(5)
            pyautogui.click(1280,1240)

            self.placed_left = False
            self.placed_mid = False
            self.placed_right = False

            from GetImage import GetGameImage
            GetGameImage(SharedData.puzzlePieceFolder,SharedData.chromeTabTitle)

            from PuzzleDetection import SearchForPuzzlePieces, SearchForPuzzleOnGrid
            SearchForPuzzlePieces(SharedData.puzzlePieceFolder, SharedData.screen_img)

            import SharedData as newData
            original_img_grid = SearchForPuzzleOnGrid(newData.screen_img, newData.screen_img_opencv)

            newData.id.display_image(original_img_grid, (457, 32, 823, 690))
            terminated = False

        return observation, info

    def close(self):
        pass


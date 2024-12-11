from math import fabs
from time import sleep
import time
import gymnasium as gym
import numpy as np
from gymnasium import spaces
import ctypes
import win32api
import os

import SharedData

cursorSpeed = 10

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

        self.action_space = spaces.Discrete(11)

        board_size = len(self.board_data)
        
        self.getPuzzleNames()

        self.observation_space = spaces.MultiDiscrete(
            [2] * len(self.board_data) + [2560, 1440] + [2] + [self.num_pieces] * 3
        )
        
        encoded_board = [
        0 if value == 'empty' else 1
        for value in self.board_data.values()
        ]

        self.holdingPiece_time = 0
        self.reward = 0
        self.holdingPiece_bool = False

    def get_mouse_position(self ):
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def move_relative(self, dx, dy):
        current_x, current_y = self.get_mouse_position()
        new_x = max(915, min(current_x + dx, 1640))
        new_y = max(70, min(current_y + dy, 1250))
        ctypes.windll.user32.SetCursorPos(new_x, new_y + dy)


    def step(self, action):

        match action:
            case 0:
                # Up
                self.move_relative(0, -cursorSpeed)
        
            case 1:
                # Down
                self.move_relative(0, cursorSpeed)
        
            case 2:
                # Left
                self.move_relative(-cursorSpeed, 0)
        
            case 3:
                # Right
                self.move_relative(cursorSpeed, 0)
        
            case 4:
                # UpLeft
                self.move_relative(-cursorSpeed, -cursorSpeed)
        
            case 5:
                # UpRight
                self.move_relative(cursorSpeed, -cursorSpeed)
        
            case 6:
                # DownLeft
                self.move_relative(-cursorSpeed, cursorSpeed)
        
            case 7:
                # DownRight
                self.move_relative(cursorSpeed, cursorSpeed)
        
            case 8:
                # LeftMouseDown
                mouseX, mouseY = self.get_mouse_position()
                if 930 <= mouseX <= 1110 and 65 <= mouseY <= 420:
                    self.reward -= 0.1
                else:
                    if not self.holdingPiece_bool:
                        self.holdingPiece_time = time.time()
                        ctypes.windll.user32.mouse_event(self.leftdown, 0, 0, 0, 0)
                        self.holdingPiece_bool = True
                    else:
                        self.reward -= 0.2
        
            case 9:
                # LeftMouseUp
                mouseX, mouseY = self.get_mouse_position()
                if (930 <= mouseX <= 1100 and 65 <= mouseY <= 420) or (1490 <= mouseX <= 1640 and 260 <= mouseY <= 440):
                    self.reward -= 0.1
                else:
                    if self.holdingPiece_bool:
                        currentTime = time.time()
                        holdTime = currentTime - self.holdingPiece_time
                        if holdTime >= 2:
                            self.reward += 0.5
                            ctypes.windll.user32.mouse_event(self.leftup, 0, 0, 0, 0)
                            self.holdingPiece_bool = False
                        else:
                            self.reward -= 0.1
                    else:
                        self.reward -= 0.2
        
            case 10:
                # Nothing
                pass

        reward = self.get_rewards(action)
        terminated = False
        truncated = False
        observation = self.get_observation()
        info = self.get_info()

        return observation, reward, terminated, truncated, info

    def get_observation(self):
        isholding = self.convertBool(self.holdingPiece_bool)
        
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
        
        observation = board_encoded + [mouse_x, mouse_y] + [isholding, left_piece_id, middle_piece_id, right_piece_id]
        
        print(observation)
        
        return np.array(observation, dtype=np.int32)


    def get_info(self):
        num_puzzle = sum(1 for value in self.board_data.values() if value == 'puzzle')
        num_empty = sum(1 for value in self.board_data.values() if value == 'empty')
        return {
            "num_puzzle": num_puzzle,
            "num_empty": num_empty
        }

    def get_rewards(self, action):

        mouseX, mouseY = self.get_mouse_position()
        if mouseX < 915 or mouseX > 1640:
            self.reward -= 1.0 
        else:
            self.reward += 0.1

        self.reward -= 0.001
        return self.reward


    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.holdingPiece_time = 0
        self.holdingPiece_bool = False
        observation = self.get_observation()
        info = self.get_info()

        return observation, info

    def close(self):
        ...


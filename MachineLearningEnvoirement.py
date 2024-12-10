from warnings import resetwarnings
import gymnasium as gym
import numpy as np
from gymnasium import spaces
import ctypes


class AnsokuEnv(gym.Env):

    def __init__(self):
        super().__init__()

        from SharedData import board_gridcell_values
        self.board_data = board_gridcell_values

        self.action_space = spaces.Discrete(5)

        board_size = len(self.board_data)
        self.observation_space = spaces.MultiDiscrete([2] * board_size + [2560, 1440])
        
        encoded_board = [
        0 if value == 'empty' else 1
        for value in self.board_data.values()
        ]

        self.reward = 0

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

        if action == 0:
            #Up
            self.move_relative(0, -5)
        elif action == 1:
            #Down
            self.move_relative(0, 5)
        elif action == 2:
            #Left
            self.move_relative(-5, 0)
        elif action == 3:
            #Right
            self.move_relative(5, 0)
        elif action == 4:
            #nothing
            self.reward += 0.01
            pass

        reward = self.get_rewards()
        terminated = False
        truncated = False
        observation = self.get_observation()
        info = self.get_info()

        return observation, reward, terminated, truncated, info

    def get_observation(self):
        # Encode the board and add mouse position
        board_encoded = [
            0 if value == 'empty' else 1
            for value in self.board_data.values()
        ]
        mouse_x, mouse_y = self.get_mouse_position()
        return np.array(board_encoded + [mouse_x, mouse_y], dtype=np.int32)


    def get_info(self):
        num_puzzle = sum(1 for value in self.board_data.values() if value == 'puzzle')
        num_empty = sum(1 for value in self.board_data.values() if value == 'empty')
        return {
            "num_puzzle": num_puzzle,
            "num_empty": num_empty
        }

    def get_rewards(self):
        mouseX, mouseY = self.get_mouse_position()
        if mouseX < 915 or mouseX > 1640:
            self.reward -= 1.0 
        else:
            self.reward += 0.1

        self.reward -= 0.01
        return self.reward



    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        observation = self.get_observation()
        info = self.get_info()

        return observation, info

    def close(self):
        ...


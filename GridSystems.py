from colorama import init, Fore, Back, Style
from PIL import Image, ImageDraw,ImageGrab
from lib2to3.pytree import convert
from webbrowser import Chrome
from GetImage import *
import numpy as np
import cv2 as cv
import os
import sys

gridColor = (252,15,192)
Letters = dict(loop_1 = "B", loop_2 = "C", loop_3 = "D", loop_4 = "E", loop_5 = "F", loop_6 = "G", loop_7 = "H", loop_8 = "I", loop_9 = "J", loop_10 = "A")

font = cv.FONT_HERSHEY_TRIPLEX
font_scale = 1
thickness = 1
def DrawGridOnImage(original_img):
    points = np.array([[1005, 450], [1550, 450],[1565, 995], [990, 995]], dtype=np.int32)
    cv.polylines(original_img, [points], isClosed=True, color=gridColor, thickness=4)
    cv.putText(original_img, Letters.get("loop_10"), ((968,498)), font, font_scale, (255, 255, 255), thickness)
    cv.putText(original_img, "1", ((1030,430)), font, font_scale, (255, 255, 255), thickness)

    lastTopTuple = [1065, 450]
    lastBottomTuple = [1060, 995]

    lastTopLeftTuple = [1005, 510]
    lastTopRightTuple = [1550, 510]

    LetterTuple_vertical = [968, 548]
    LetterTuple_horizontal = [1080, 430]
    for _ in range(9):
        horizontalLine = np.array([lastBottomTuple, lastTopTuple], dtype=np.int32)
        cv.polylines(original_img, [horizontalLine], isClosed=True, color=gridColor, thickness=4)
        cv.putText(original_img, f"{_ + 2}", (LetterTuple_horizontal), font, font_scale, (255, 255, 255), thickness)

        verticalLine = np.array([lastTopLeftTuple, lastTopRightTuple], dtype=np.int32)
        cv.polylines(original_img, [verticalLine], isClosed=True, color=gridColor, thickness=4)
        cv.putText(original_img, Letters.get(f"loop_{_ + 1}"), (LetterTuple_vertical), font, font_scale, (255, 255, 255), thickness)

        if _ <= 4:
            lastTopTuple[0] += 55
            lastBottomTuple[0] += 56

            lastTopLeftTuple[1] += 54
            lastTopRightTuple[1] += 54

            LetterTuple_vertical[1] += 54
            LetterTuple_horizontal[0] += 54
        elif _ <= 6:
            lastTopTuple[0] += 50
            lastBottomTuple[0] += 58

            lastTopLeftTuple[1] += 54
            lastTopRightTuple[1] += 54

            LetterTuple_vertical[1] += 54
            LetterTuple_horizontal[0] += 54
        elif _ <= 8:
            lastTopTuple[0] += 53
            lastBottomTuple[0] += 50

            lastTopLeftTuple[1] += 56
            lastTopRightTuple[1] += 56

            LetterTuple_vertical[1] += 56
            LetterTuple_horizontal[0] += 47

    return original_img
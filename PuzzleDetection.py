from multiprocessing import sharedctypes
from lib2to3.pytree import convert
from webbrowser import Chrome
from GetImage import *
from math import sqrt
import SharedData
from CommonImports import *
from concurrent.futures import ThreadPoolExecutor, as_completed

# Use the same ConsoleRedirect instance if provided
if hasattr(sys.modules[__name__], 'console_redirect'):
    sys.stdout = sys.modules[__name__].console_redirect
    sys.stderr = sys.modules[__name__].console_redirect

# Initialize colorama with the same settings
init(strip=False, convert=False, autoreset=True)

#Text Settings for rectangle text
font = cv.FONT_HERSHEY_TRIPLEX
font_scale = 0.3
thickness = 1

currentPuzzlePieces = None

def process_file(file_path, variantResized_img, matchingImageThreshold):
    imageWithoutExtension, _ = os.path.splitext(os.path.basename(file_path))
    
    puzzlePiece_img = cv.imread(file_path, cv.IMREAD_REDUCED_COLOR_2)

    result = cv.matchTemplate(variantResized_img, puzzlePiece_img, cv.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)

    if max_val >= matchingImageThreshold:
        print(Fore.GREEN + f"{imageWithoutExtension} matches with a percentage of {round(max_val * 100, 1)}%")
        return {
            "name": imageWithoutExtension,
            "dictTop_left": max_loc,
            "dictBottom_right": (max_loc[0] + puzzlePiece_img.shape[1], max_loc[1] + puzzlePiece_img.shape[0]),
            "max_val": max_val,
            "image": puzzlePiece_img
        }
    else:
            print(Fore.RED + f"{imageWithoutExtension} didn't match. Its match percentage was {round(max_val * 100, 1)}%")
    return None

def SearchForPuzzlePieces(ImageFolder, scanImage):

    currentPuzzlePieces = dict(puzzlePiece_left = "Empty", puzzlePiece_middle = "Empty", puzzlePiece_right = "Empty")
    matchingImageThreshold = 0.75
    image_variants = []

    #convert pillow screenshot to opencv image
    scanImage_cv = np.array(scanImage)
    scanImage_cv = cv.cvtColor(scanImage_cv, cv.COLOR_RGB2BGR)

    original_img = scanImage_cv

    #Draw the Grid System
    from GridSystems import DrawGridOnImage
    original_img = DrawGridOnImage(original_img)

    original_height, original_width = original_img.shape[:2]
    new_width, new_height = original_width // 2, original_height // 2
    original_img = cv.resize(original_img, (new_width, new_height))

    #use pillow library Image functione to get a image
    img = scanImage
    SharedData.screen_img = scanImage
    #Manually set tuple(a kind of vector2) to later use to cover image
    SharedData.image_variants = variants = [
        [((1220, 1040), (1355, 1200)), ((1355, 1040), (1500, 1200)), ((0, 0), (1060, 1440)), ((0, 0), (2560, 1050)), ((0, 1200), (2560, 1440)), ((1500, 1040), (2560, 1440))],
        [((1040, 1040), (1200, 1200)), ((1355, 1040), (1500, 1200)), ((0, 0), (1060, 1440)), ((0, 0), (2560, 1050)), ((0, 1200), (2560, 1440)), ((1500, 1040), (2560, 1440))],
        [((1040, 1040), (1200, 1200)), ((1200, 1040), (1355, 1200)), ((0, 0), (1060, 1440)), ((0, 0), (2560, 1050)), ((0, 1200), (2560, 1440)), ((1500, 1040), (2560, 1440))]
    ]

    #creates an alternate image and covers some places with black to make sure that the image recognition is more accurate
    for i, rects in enumerate(variants, 1):
        variant_img = img.copy()
        draw = ImageDraw.Draw(variant_img)
    
        for rect in rects:
            draw.rectangle(rect, fill="black")
    
        image_variants.append(variant_img)


    for variant_img in image_variants:
        mostMatchingPiece = {"name": "Empty", "dictTop_left": 0, "dictBottom_right": 0, "max_val": 0, "image": None}

        if variant_img == image_variants[0]:
            print(Fore.WHITE + f"Scanning first Puzzle")
        elif variant_img == image_variants[1]:
            print(Fore.WHITE + f"Scanning Second Puzzle")
        elif variant_img == image_variants[2]:
            print(Fore.WHITE + f"Scanning Third Puzzle")

        variant_img_cv = np.array(variant_img)
        variant_img_cv = cv.cvtColor(variant_img_cv, cv.COLOR_RGB2BGR)
        original_height, original_width = variant_img_cv.shape[:2]
        new_width, new_height = original_width // 2, original_height // 2
        variantResized_img = cv.resize(variant_img_cv, (new_width, new_height))

        files_to_process = []
        for root, _, files in os.walk(ImageFolder):
            files_to_process.extend([os.path.join(root, file) for file in files if file.endswith(".png")])

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(process_file, file_path, variantResized_img, matchingImageThreshold): file_path for file_path in files_to_process}
            for future in as_completed(futures):
                result = future.result()
                if result and result["max_val"] > mostMatchingPiece["max_val"]:
                    mostMatchingPiece = result


        if(mostMatchingPiece.get("name") != "Empty"):
            
            #Get the center of the best matching piece to add text to the rectangle for extra debugging info
            center_x = (mostMatchingPiece.get("dictTop_left")[0] + mostMatchingPiece.get("dictBottom_right")[0]) // 2
            center_y = (mostMatchingPiece.get("dictTop_left")[1] + mostMatchingPiece.get("dictBottom_right")[1]) // 2

            text_size = cv.getTextSize(mostMatchingPiece.get("name"), font, font_scale, thickness)[0]
            text_width, text_height = text_size

            #Set text to center
            text_x = center_x - (text_width // 2)
            text_y = center_y + (text_height // 2)

            cv.rectangle(original_img, mostMatchingPiece.get("dictTop_left"), mostMatchingPiece.get("dictBottom_right"), color=(0,200,0), thickness=2, lineType=cv.LINE_4)
            cv.putText(original_img, mostMatchingPiece.get("name"), (text_x, text_y), font, font_scale, (0, 0, 0), thickness)
            #print(Fore.WHITE + str(mostMatchingPiece))

        if variant_img == image_variants[0]:
            currentPuzzlePieces["puzzlePiece_left"] = mostMatchingPiece.get("name");
            SharedData.PuzzleImage1 = mostMatchingPiece.get("image")
        elif variant_img == image_variants[1]:
            currentPuzzlePieces["puzzlePiece_middle"] = mostMatchingPiece.get("name");
            SharedData.PuzzleImage2 = mostMatchingPiece.get("image")
        elif variant_img == image_variants[2]:
            currentPuzzlePieces["puzzlePiece_right"] = mostMatchingPiece.get("name");
            SharedData.PuzzleImage3 = mostMatchingPiece.get("image")

        SharedData.currentPuzzlePieces = currentPuzzlePieces
        SharedData.screen_img_opencv = original_img

board_gridcell_values = dict(A1 = (1044,470), A2 = (1105,470), A3 = (1155,470), A4 = (1210,470), A5 = (1270,470), A6 = (1320,470), A7 = (1376,470), A8 = (1415,470), A9 = (1468,470), A10 = (1528,470)
, B1 = (1040,525), B2 = (1105,523), B3 = (1155,525), B4 = (1210,525), B5 = (1262,525), B6 = (1320,525), B7 = (1378,525), B8 = (1408,525), B9 = (1463,525), B10 = (1520,525)
, C1 = (1040,580), C2 = (1105,580), C3 = (1155,580), C4 = (1210,580), C5 = (1265,580), C6 = (1320,580), C7 = (1370,595), C8 = (1415,580), C9 = (1470,580), C10 = (1523,580)
, D1 = (1040,635), D2 = (1105,635), D3 = (1155,635), D4 = (1210,635), D5 = (1262,635), D6 = (1320,635), D7 = (1370,635), D8 = (1425,635), D9 = (1470,635), D10 = (1528,635)
, E1 = (1040,690), E2 = (1105,690), E3 = (1155,690), E4 = (1210,690), E5 = (1265,690), E6 = (1320,690), E7 = (1370,690), E8 = (1420,690), E9 = (1475,690), E10 = (1533,690)
, F1 = (1040,745), F2 = (1105,745), F3 = (1155,745), F4 = (1210,745), F5 = (1262,745), F6 = (1320,745), F7 = (1358,745), F8 = (1420,745), F9 = (1480,745), F10 = (1533,745)
, G1 = (1040,795), G2 = (1100,795), G3 = (1155,795), G4 = (1210,795), G5 = (1262,795), G6 = (1320,795), G7 = (1375,795), G8 = (1415,795), G9 = (1471,795), G10 = (1540,795)
, H1 = (1040,849), H2 = (1100,849), H3 = (1155,849), H4 = (1210,849), H5 = (1270,849), H6 = (1325,849), H7 = (1382,849), H8 = (1415,849), H9 = (1470,849), H10 = (1525,849)
, I1 = (1040,905), I2 = (1098,905), I3 = (1155,905), I4 = (1210,905), I5 = (1262,905), I6 = (1320,905), I7 = (1380,905), I8 = (1415,905), I9 = (1470,905), I10 = (1530,905)
, J1 = (1040,955), J2 = (1100,960), J3 = (1150,960), J4 = (1210,955), J5 = (1262,957), J6 = (1320,957), J7 = (1370,957), J8 = (1425,957), J9 = (1480,957), J10 = (1540,957))

gridCell_value_empty = dict(A1 = (194, 178, 178), A2 = (209, 191, 190), A3 = (217, 200, 199), A4 = (223, 205, 204), A5 = (226, 207, 207), A6 = (225, 207, 206), A7 = (222, 204, 203), A8 = (212, 196, 195), A9 = (203, 187, 187), A10 = (193, 177, 176)
, B1 = (196, 181, 180), B2 = (212, 195, 195), B3 = (224, 205, 204), B4 = (230, 210, 210), B5 = (232, 212, 213), B6 = (227, 209, 209), B7 = (219, 202, 201), B8 = (219, 202, 200), B9 = (206, 190, 189), B10 = (194, 178, 179)
, C1 = (200, 184, 184), C2 = (217, 199, 198), C3 = (227, 209, 207), C4 = (232, 213, 213), C5 = (235, 215, 216), C6 = (231, 212, 213), C7 = (231, 212, 212), C8 = (224, 204, 204), C9 = (212, 194, 193), C10 = (199, 183, 182)
, D1 = (209, 192, 190), D2 = (221, 203, 202), D3 = (234, 214, 214), D4 = (238, 217, 219), D5 = (242, 220, 223), D6 = (237, 216, 218), D7 = (238, 217, 218), D8 = (230, 211, 210), D9 = (220, 202, 201), D10 = (207, 189, 187)
, E1 = (209, 192, 190), E2 = (220, 202, 201), E3 = (234, 214, 214), E4 = (239, 218, 219), E5 = (243, 221, 224), E6 = (238, 217, 219), E7 = (239, 218, 219), E8 = (231, 211, 211), E9 = (221, 202, 201), E10 = (209, 191, 189)
, F1 = (210, 192, 190), F2 = (219, 202, 201), F3 = (232, 212, 213), F4 = (237, 217, 218), F5 = (241, 220, 222), F6 = (237, 217, 219), F7 = (237, 215, 217), F8 = (230, 210, 210), F9 = (220, 202, 200), F10 = (207, 189, 188)
, G1 = (207, 190, 189), G2 = (217, 199, 199), G3 = (228, 209, 209), G4 = (233, 214, 215), G5 = (238, 217, 219), G6 = (234, 214, 216), G7 = (234, 214, 215), G8 = (227, 208, 208), G9 = (217, 199, 197), G10 = (197, 181, 181)
, H1 = (205, 189, 187), H2 = (214, 196, 196), H3 = (226, 207, 207), H4 = (231, 212, 213), H5 = (233, 213, 215), H6 = (227, 209, 210), H7 = (223, 206, 205), H8 = (225, 206, 205), H9 = (214, 196, 195), H10 = (198, 182, 182)
, I1 = (202, 185, 184), I2 = (209, 193, 192), I3 = (222, 204, 203), I4 = (228, 209, 209), I5 = (233, 213, 214), I6 = (230, 211, 212), I7 = (229, 210, 209), I8 = (222, 204, 203), I9 = (212, 195, 194), I10 = (197, 180, 180)
, J1 = (196, 180, 179), J2 = (207, 190, 190), J3 = (220, 202, 201), J4 = (221, 204, 203), J5 = (227, 209, 208), J6 = (225, 206, 207), J7 = (223, 205, 205), J8 = (217, 199, 198), J9 = (206, 189, 188), J10 = (192, 176, 175))

gridCell_value_puzzle = dict(A1 = (182, 171, 170), A2 = (195, 183, 182), A3 = (203, 191, 189), A4 = (208, 196, 195), A5 = (211, 198, 197), A6 = (210, 198, 197), A7 = (205, 193, 191), A8 = (201, 189, 187), A9 = (192, 180, 180), A10 = (179, 169, 167)
, B1 = (185, 174, 173), B2 = (198, 186, 185), B3 = (206, 194, 192), B4 = (212, 199, 198), B5 = (213, 201, 199), B6 = (213, 201, 199), B7 = (209, 197, 195), B8 = (206, 193, 192), B9 = (197, 185, 184), B10 = (182, 171, 170)
, C1 = (188, 176, 175), C2 = (201, 189, 188), C3 = (209, 197, 195), C4 = (215, 202, 200), C5 = (217, 204, 202), C6 = (216, 203, 202), C7 = (213, 200, 199), C8 = (206, 194, 192), C9 = (198, 186, 185), C10 = (185, 174, 172)
, D1 = (190, 178, 177), D2 = (203, 191, 190), D3 = (211, 199, 197), D4 = (216, 204, 202), D5 = (219, 206, 204), D6 = (218, 205, 204), D7 = (215, 202, 201), D8 = (201, 189, 187), D9 = (200, 188, 187), D10 = (187, 175, 174)
, E1 = (191, 179, 178), E2 = (204, 192, 190), E3 = (212, 200, 198), E4 = (217, 205, 203), E5 = (220, 207, 206), E6 = (219, 206, 205), E7 = (210, 198, 196), E8 = (210, 197, 196), E9 = (199, 187, 186), E10 = (188, 176, 175)
, F1 = (192, 179, 178), F2 = (205, 192, 191), F3 = (213, 200, 198), F4 = (217, 205, 203), F5 = (220, 207, 206), F6 = (219, 206, 205), F7 = (216, 203, 202), F8 = (210, 197, 196), F9 = (199, 187, 186), F10 = (188, 176, 175)
, G1 = (191, 179, 179), G2 = (204, 192, 191), G3 = (212, 199, 198), G4 = (218, 204, 202), G5 = (220, 206, 205), G6 = (218, 205, 204), G7 = (215, 202, 201), G8 = (210, 197, 196), G9 = (198, 187, 185), G10 = (185, 174, 172)
, H1 = (189, 178, 177), H2 = (203, 191, 189), H3 = (211, 198, 197), H4 = (216, 202, 202), H5 = (218, 204, 203), H6 = (216, 203, 202), H7 = (212, 200, 198), H8 = (208, 196, 194), H9 = (199, 187, 186), H10 = (187, 176, 174)
, I1 = (188, 176, 175), I2 = (199, 187, 186), I3 = (208, 195, 194), I4 = (213, 201, 199), I5 = (216, 203, 201), I6 = (215, 201, 200), I7 = (212, 198, 197), I8 = (204, 192, 190), I9 = (196, 184, 183), I10 = (183, 172, 171)
, J1 = (185, 173, 172), J2 = (196, 185, 183), J3 = (204, 192, 191), J4 = (210, 197, 196), J5 = (212, 200, 198), J6 = (211, 198, 198), J7 = (208, 195, 193), J8 = (200, 188, 187), J9 = (191, 179, 178), J10 = (177, 167, 166))

def get_color_distance(pixel, target_color):
    return sqrt(sum((pixel[i] - target_color[i]) ** 2 for i in range(3)))

def SearchForPuzzleOnGrid(original_img, cvImage):

    board_gridcell_values = dict(A1 = (1044,470), A2 = (1105,470), A3 = (1155,470), A4 = (1210,470), A5 = (1270,470), A6 = (1320,470), A7 = (1376,470), A8 = (1415,470), A9 = (1468,470), A10 = (1528,470)
    , B1 = (1040,525), B2 = (1105,523), B3 = (1155,525), B4 = (1210,525), B5 = (1262,525), B6 = (1320,525), B7 = (1378,525), B8 = (1408,525), B9 = (1463,525), B10 = (1520,525)
    , C1 = (1040,580), C2 = (1105,580), C3 = (1155,580), C4 = (1210,580), C5 = (1265,580), C6 = (1320,580), C7 = (1370,595), C8 = (1415,580), C9 = (1470,580), C10 = (1523,580)
    , D1 = (1040,635), D2 = (1105,635), D3 = (1155,635), D4 = (1210,635), D5 = (1262,635), D6 = (1320,635), D7 = (1370,635), D8 = (1425,635), D9 = (1470,635), D10 = (1528,635)
    , E1 = (1040,690), E2 = (1105,690), E3 = (1155,690), E4 = (1210,690), E5 = (1265,690), E6 = (1320,690), E7 = (1370,690), E8 = (1420,690), E9 = (1475,690), E10 = (1533,690)
    , F1 = (1040,745), F2 = (1105,745), F3 = (1155,745), F4 = (1210,745), F5 = (1262,745), F6 = (1320,745), F7 = (1358,745), F8 = (1420,745), F9 = (1480,745), F10 = (1533,745)
    , G1 = (1040,795), G2 = (1100,795), G3 = (1155,795), G4 = (1210,795), G5 = (1262,795), G6 = (1320,795), G7 = (1375,795), G8 = (1415,795), G9 = (1471,795), G10 = (1540,795)
    , H1 = (1040,849), H2 = (1100,849), H3 = (1155,849), H4 = (1210,849), H5 = (1270,849), H6 = (1325,849), H7 = (1382,849), H8 = (1415,849), H9 = (1470,849), H10 = (1525,849)
    , I1 = (1040,905), I2 = (1098,905), I3 = (1155,905), I4 = (1210,905), I5 = (1262,905), I6 = (1320,905), I7 = (1380,905), I8 = (1415,905), I9 = (1470,905), I10 = (1530,905)
    , J1 = (1040,955), J2 = (1100,960), J3 = (1150,960), J4 = (1210,955), J5 = (1262,957), J6 = (1320,957), J7 = (1370,957), J8 = (1425,957), J9 = (1480,957), J10 = (1540,957))

    target_static_colors = {
        "shadow1": (153, 147, 150),
        "shadow2": (184, 173, 177),
        "shadow3": (135, 128, 137),
        "shadow4": (176, 164, 167),
        "shadow5": (196, 184, 186),
        "shadow6": (203, 188, 190),
        "void": (0, 0, 0),
    }

    original_height, original_width = cvImage.shape[:2]
    new_width, new_height = original_width * 2, original_height * 2
    cvImage = cv.resize(cvImage, (new_width, new_height))

    for cell, position in board_gridcell_values.items():
        if position != (0, 0):

            px = original_img.getpixel(position)

            target_colors = target_static_colors.copy()
            target_colors["empty"] = gridCell_value_empty[cell]
            target_colors["puzzle"] = gridCell_value_puzzle[cell]

            distances = {label: get_color_distance(px, color) for label, color in target_colors.items()}
            print(Fore.LIGHTCYAN_EX + f"{cell}: {px}")
            #print(Fore.LIGHTCYAN_EX + f"{cell} = {px}, ")
            closest_label = min(distances, key=distances.get)

            #print(Fore.LIGHTCYAN_EX + f"Closest match: {closest_label}")
            if closest_label == "puzzle":

                cv.circle(cvImage, (position[0], position[1]), radius=3, color=(0, 220, 0), thickness=3)
                print(Fore.LIGHTGREEN_EX + f"{cell} is a puzzle")
                board_gridcell_values[str(cell)] = "puzzle"

            elif closest_label == "empty":

                print(Fore.LIGHTBLUE_EX + f"{cell} is empty")
                cv.circle(cvImage, (position[0], position[1]), radius=3, color=(220, 0, 0), thickness=3)
                board_gridcell_values[str(cell)] = "empty"

            elif closest_label == "shadow1":

                print(Fore.LIGHTBLACK_EX + f"{cell} is shadow")
                cv.circle(cvImage, (position[0], position[1]), radius=3, color=(0, 0, 0), thickness=3)
                board_gridcell_values[str(cell)] = "empty"

            elif closest_label == "shadow2":

                print(Fore.LIGHTBLACK_EX + f"{cell} is shadow")
                cv.circle(cvImage, (position[0], position[1]), radius=3, color=(0, 0, 0), thickness=3)
                board_gridcell_values[str(cell)] = "empty"

            elif closest_label == "shadow3":

                print(Fore.LIGHTBLACK_EX + f"{cell} is shadow")
                cv.circle(cvImage, (position[0], position[1]), radius=3, color=(0, 0, 0), thickness=3)
                board_gridcell_values[str(cell)] = "empty"

            elif closest_label == "shadow4":

                print(Fore.LIGHTBLACK_EX + f"{cell} is shadow")
                cv.circle(cvImage, (position[0], position[1]), radius=3, color=(0, 0, 0), thickness=3)
                board_gridcell_values[str(cell)] = "empty"

            elif closest_label == "shadow5":

                print(Fore.LIGHTBLACK_EX + f"{cell} is shadow")
                cv.circle(cvImage, (position[0], position[1]), radius=3, color=(0, 0, 0), thickness=3)
                board_gridcell_values[str(cell)] = "empty"

            elif closest_label == "shadow6":

                print(Fore.LIGHTBLACK_EX + f"{cell} is shadow")
                cv.circle(cvImage, (position[0], position[1]), radius=3, color=(0, 0, 0), thickness=3)
                board_gridcell_values[str(cell)] = "empty"
    

    original_height, original_width = cvImage.shape[:2]
    new_width, new_height = original_width // 2, original_height // 2
    cvImage = cv.resize(cvImage, (new_width, new_height))

    #print(Fore.MAGENTA + str(board_gridcell_values))

    SharedData.board_gridcell_values = board_gridcell_values

    return cvImage







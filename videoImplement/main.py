import os
import cv2
import shutil
import datetime
import splitVideo
# make sure later u save the detected images into a folder

pathToVideo = "../eyeVids/pupil_video_2.mp4"
pathToLeft = "./videos/left_half.mp4"
pathToRight = "./videos/right_half.mp4"


# print stuff with timestamp at the start cuz it looks nice
# lmao
def dprint(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def splitEyes(video, left, right, widthThresh):
    dprint(f"attemping to convert video file '{video} into left and right videos '{left}' and '{right}'")
    # Paths
    input_video = video  # path to video
    output_left = left
    output_right = right

    splitVideo.split_video_left_right(input_video, output_left, output_right, widthThresh)



def resetFolder(folderName):
    if os.path.exists(folderName):
        dprint(f"folder '{folderName}' exists, removing contents in folder")
        try:
            shutil.rmtree(folderName)
            dprint(f"Folder '{folderName}' and all its contents deleted successfully.")
        except OSError as e:
            dprint(f"Error: {e}. An error occurred during deletion.")
        dprint(f"Making new '{folderName}'")
        os.makedirs(folderName)
    else: 
        dprint(f"Folder '{folderName}' does not exist, making the folder")
        try:
            os.makedirs(folderName)
        except OSError:
            dprint(f"Error: Creating folder '{folderName}'")


# split the video into multiple image files
def videoToImages(video, folderName):
    folderName = str(folderName)
    dprint(f"Trying to convert video '{video}' into frames and storing into '{folderName}'")
    # 2. convert the video into multiple .bmp files and store it in the tempImages folder
    cam = cv2.VideoCapture(video)
    currentframe = 0

    while True:
        ret,frame = cam.read()
        if ret:
            name = './frames/' + folderName +'/frame' + str(currentframe) + '.jpg'
            dprint("Creating... " + name)

            cv2.imwrite(name, frame)

            currentframe += 1
        else:
            break

    cam.release()
    cv2.destroyAllWindows()    
    dprint("All frames done!")
    # 3. turn images ito grayscale (actually i think this is part of the algorithm but meh)
    
def pupilDetection():
    pass

def blinkDetection(image):
    pass


# ENTRY POITN!!!

resetFolder("videos")
splitEyes(pathToVideo, pathToLeft, pathToRight, 600)
resetFolder("frames")
resetFolder("frames/left")
resetFolder("frames/right")
videoToImages(pathToLeft,"left")
videoToImages(pathToRight,"right")
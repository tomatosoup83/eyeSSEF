# TODO
# add a counter for processing iterations?
# set data as bad if confidence < threshold
# set data as bad IF the difference in pupil diameter between any 2 frames is >0.5mm (applies for 60fps)
# do cubic spline interpolation to fill in bad data points



import os
import cv2
import shutil
import datetime
import scripts.others.splitVideo as splitVideo
import scripts.detection.ppDetect as ppDetect
import scripts.others.graph as graph
import scripts.others.util as util
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import CubicSpline

#from scripts.preProcessing.firstPass import preProcessFirstPass
# make sure later u save the detected images into a folder

pathToVideo = "../eyeVids/tuna/PLR_Tuna_R_1920x1080_30_3.mp4"
pathToLeft = "./videos/left_half.mp4"
pathToRight = "./videos/right_half.mp4"
confidenceThresh = 0.75

processingIteration = 0
pxToMm = 30 # for 1080p



# print stuff with timestamp at the start cuz it looks nice
# lmao


def splitEyes(video, left, right, widthThresh):
    util.dprint(f"attemping to convert video file '{video} into left and right videos '{left}' and '{right}'")
    # Paths
    input_video = video  # path to video
    output_left = left
    output_right = right

    splitVideo.split_video_left_right(input_video, output_left, output_right, widthThresh)



def resetFolder(folderName):
    if os.path.exists(folderName):
        util.dprint(f"folder '{folderName}' exists, removing contents in folder")
        try:
            shutil.rmtree(folderName)
            util.dprint(f"Folder '{folderName}' and all its contents deleted successfully.")
        except OSError as e:
            util.dprint(f"Error: {e}. An error occurred during deletion.")
        util.dprint(f"Making new '{folderName}'")
        os.makedirs(folderName)
    else: 
        util.dprint(f"Folder '{folderName}' does not exist, making the folder")
        try:
            os.makedirs(folderName)
        except OSError:
            util.dprint(f"Error: Creating folder '{folderName}'")
    return folderName

# split the video into multiple image files
def videoToImages(video, folderName):
    folderName = str(folderName)
    util.dprint(f"Trying to convert video '{video}' into frames and storing into '{folderName}'")
    # 2. convert the video into multiple .bmp files and store it in the tempImages folder
    cam = cv2.VideoCapture(video)
    currentframe = 0
    frameRate = cam.get(cv2.CAP_PROP_FPS)
    print(f"Video frame rate: {frameRate} fps")
    while True:
        ret,frame = cam.read()
        if ret:
            #name = './frames/' + folderName +'/frame' + str(currentframe) + '.bmp'
            name = os.path.join(folderName, 'frame' + str(currentframe) + '.bmp')
            util.dprint("Creating... " + name)

            cv2.imwrite(name, frame)

            currentframe += 1
        else:
            break

    cam.release()
    cv2.destroyAllWindows()    
    util.dprint("All frames done!")

    return frameRate, currentframe

    # 3. turn images ito grayscale (actually i think this is part of the algorithm but meh)
    
def pupilDetectionInFolder(folderPath):
    util.dprint(f"Starting pupil detection in folder '{folderPath}'")
    conf = []
    diameter = []
    for i in range(len(os.listdir(folderPath))):
        filename = f"frame{i}.bmp"
        newPath = os.path.join(folderPath, filename)
        imgWithPupil, outline_confidence, pupil_diameter = ppDetect.detect(newPath)
        
        conf.append(outline_confidence)
        diameter.append(pupil_diameter)
        util.dprint(f"Showing image {newPath} with detected pupil...")
        # show the images continuously using cv2 window
        cv2.imshow("Pupil Detection for " + pathToVideo, imgWithPupil)
        cv2.waitKey(1)  # Display each image for 1 ms

        # closes window after all images are shown
    cv2.destroyAllWindows()
    return conf, diameter

def calculateTimeStamps(frameRate, totalFrames):
    timePerFrame = 1.0 / frameRate
    timestamps = [i * timePerFrame for i in range(totalFrames)]
    return timestamps


def getAverageOfColumn(dataframe, colName):
    return dataframe[colName].mean()



def blinkDetection(image):
    pass

# save data to csv with Columns: 'frame_id', 'timestamp', 'diameter', 'diameter_mm', 'confidence', 'is_bad_data'
def saveDataToCSV(frameIDs, timestamps, diameters, confidences, outputPath):
    data = {
        'frame_id': frameIDs,
        'timestamp': timestamps,
        'diameter': diameters,
        'confidence': confidences
    }
    df = pd.DataFrame(data)
    # Mark bad data points (confidence < 1)
    df['is_bad_data'] = df['confidence'] < confidenceThresh
    df['diameter_mm'] = df['diameter'] / pxToMm
    df.to_csv(outputPath, index=False)
    util.dprint(f"Data saved to CSV at '{outputPath}'")
    
    # return the pandas dataframe too if needed
    return df




def generateReport():
    util.dprint("Running standalone pupil detection implementation...")
    resetFolder("videos")
    #splitEyes(pathToVideo, pathToLeft, pathToRight, 600)
    resetFolder("frames")
    #resetFolder("frames/left")
    #resetFolder("frames/right")
    #videoToImages(pathToLeft,"left")
    #videoToImages(pathToRight,"right")
    frameRate, totalFrames = videoToImages(pathToVideo,"frames")

    #pupilDetectionInFolder("frames/left/")
    #pupilDetectionInFolder("frames/right/")
    conf, diameter = pupilDetectionInFolder("frames/")



    timestamps = calculateTimeStamps(frameRate, totalFrames)
    dataFolderPath = resetFolder("data/"+os.path.basename(pathToVideo).split('.')[0])
    csvDataPath = "data/" + os.path.basename(pathToVideo).split('.')[0] + "/raw.csv"
    df = saveDataToCSV(list(range(totalFrames)), timestamps, diameter, conf, csvDataPath)
    print(("Average pupil diameter (pixels): ", getAverageOfColumn(df, 'diameter')))
    graph.plotResults(df, savePath=dataFolderPath + "/rawPlot.png", showPlot=True, showMm=True)

    # first pass preprocessing
    #df = preProcessFirstPass(df)
    # save the preprocessed data too
    #csvPreprocessedPath = "data/" + os.path.basename(pathToVideo).split('.')[0] + "/firstPass.csv"
    #df.to_csv(csvPreprocessedPath, index=False)
    #print(f"Preprocessed data saved to CSV at '{csvPreprocessedPath}'")
    #print(type(df))
    #plotResults(df, savePath=dataFolderPath + "/firstPassPlot.png", showPlot=True, showMm=True)


# ENTRY POITN!!!
if __name__ == "__main__":
    generateReport()

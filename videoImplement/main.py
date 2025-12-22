# TODO
# add a counter for processing iterations?
# set data as bad if confidence < threshold
# set data as bad IF the difference in pupil diameter between any 2 frames is >0.5mm (applies for 60fps)
# do cubic spline interpolation to fill in bad data points



import os
import cv2
import shutil
import datetime
import splitVideo
import ppDetect
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import CubicSpline
# make sure later u save the detected images into a folder

pathToVideo = "../eyeVids/PLR_Calibration_R_1920x1080_30_3.mp4"
pathToLeft = "./videos/left_half.mp4"
pathToRight = "./videos/right_half.mp4"
confidenceThresh = 0.9

processingIteration = 0


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
    return folderName

# split the video into multiple image files
def videoToImages(video, folderName):
    folderName = str(folderName)
    dprint(f"Trying to convert video '{video}' into frames and storing into '{folderName}'")
    # 2. convert the video into multiple .bmp files and store it in the tempImages folder
    cam = cv2.VideoCapture(video)
    currentframe = 0
    frameRate = cam.get(cv2.CAP_PROP_FPS)
    while True:
        ret,frame = cam.read()
        if ret:
            #name = './frames/' + folderName +'/frame' + str(currentframe) + '.bmp'
            name = os.path.join(folderName, 'frame' + str(currentframe) + '.bmp')
            dprint("Creating... " + name)

            cv2.imwrite(name, frame)

            currentframe += 1
        else:
            break

    cam.release()
    cv2.destroyAllWindows()    
    dprint("All frames done!")

    return frameRate, currentframe

    # 3. turn images ito grayscale (actually i think this is part of the algorithm but meh)
    
def pupilDetectionInFolder(folderPath):
    dprint(f"Starting pupil detection in folder '{folderPath}'")
    conf = []
    diameter = []
    for i in range(len(os.listdir(folderPath))):
        filename = f"frame{i}.bmp"
        newPath = os.path.join(folderPath, filename)
        imgWithPupil, outline_confidence, pupil_diameter = ppDetect.detect(newPath)
        
        conf.append(outline_confidence)
        diameter.append(pupil_diameter)
        dprint(f"Showing image {newPath} with detected pupil...")
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






def blinkDetection(image):
    pass

# save data to csv with Columns: 'frame_id', 'timestamp', 'diameter', 'confidence'
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
    df.to_csv(outputPath, index=False)
    dprint(f"Data saved to CSV at '{outputPath}'")
    
    # return the pandas dataframe too if needed
    return df
def plotResults(dataframe, savePath=None, showPlot=True):
    # clear previous plots
    plt.clf()
    # plot data based on dataframe
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(dataframe['timestamp'], dataframe['diameter'], label='Pupil Diameter (pixels)', color='blue')
    plt.xlabel('Time (s)')
    plt.ylabel('Diameter (pixels)')
    plt.title('Pupil Diameter Over Time')
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.plot(dataframe['timestamp'], dataframe['confidence'], label='Confidence', color='green')
    plt.xlabel('Time (s)')
    plt.ylabel('Confidence')
    plt.title('Detection Confidence Over Time')
    plt.legend()
    
    plt.tight_layout()
    if savePath:
        plt.savefig(savePath)
        dprint(f"Plot saved to '{savePath}'")
    if showPlot:
        plt.show()

def preProcessData(df):
    # set rows with confidence < 1 to NaN
    dprint("Preprocessing data: setting diameters with confidence < 1 to NaN")
    df.loc[df['confidence'] < confidenceThresh, 'diameter'] = float('nan')
    return df

def interpolateBadData(df):

    pass


# ENTRY POITN!!!

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
plotResults(df, savePath=dataFolderPath + "/rawPlot.png", showPlot=False)
df = preProcessData(df)
# save the preprocessed data too
csvPreprocessedPath = "data/" + os.path.basename(pathToVideo).split('.')[0] + "/preprocessed.csv"
df.to_csv(csvPreprocessedPath, index=False)
#print(f"Preprocessed data saved to CSV at '{csvPreprocessedPath}'")
print(type(df))
plotResults(df, savePath=dataFolderPath + "/processedPlot.png", showPlot=True)
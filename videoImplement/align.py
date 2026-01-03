# calculating PLR metrics
# in the first 5 seconds find the biggest dip as the first constriction (when blue light stimuli is on)
# baseline is 1 second before the first stimuli onset

# approximation of data points: 3s baseline - 0.25s blue - 60s rest - 0.25s red - 60s rest (might vary cuz fps)
# maybe can add a bit of buffer time to be safe
import pandas as pd

import scripts.others.util as util
import scripts.others.graph as graph

# load the dataframe
util.dprint("Loading processed data for PLR metrics calculation")
df1Path = "../videoImplement/data/PLR_Tuna_R_1920x1080_30_4/"
df = pd.read_csv(df1Path + 'processed.csv')

vidFps = 30

# find the first constriction
def lowestDip(startingIndex=0, fps=vidFps):
    diameterMM = df['diameter_mm'].values
    timestamp = df['timestamp'].values

    # find lowest point in first 5 seconds
    searchDuration = 5.0 # seconds
    searchFrames = int(searchDuration * fps)
    minDiameter = float('inf')
    minIndex = -1
    for i in range(startingIndex, min(startingIndex + searchFrames, len(diameterMM))):
        if not pd.isna(diameterMM[i]) and diameterMM[i] < minDiameter:
            minDiameter = diameterMM[i]
            minIndex = i

    util.dprint(f"Lowest dip found at index {minIndex} with diameter {minDiameter} mm at time {timestamp[minIndex]} s")
    return minIndex

# approximate baseline to be 1.5s before the constriction
def findBaseline(dipIndex, fps=vidFps):
    diameterMM = df['diameter_mm'].values
    timestamp = df['timestamp'].values

    onsetOffsetFrames = int(1.5 * fps)
    onsetIndex = max(0, dipIndex - onsetOffsetFrames)

    util.dprint(f"Baseline onset approximated at index {onsetIndex} with diameter {diameterMM[onsetIndex]} mm at time {timestamp[onsetIndex]} s")
    return onsetIndex


# find start of transient PLR as the first point where the difference between this point and the next point exceeds a threshold
def findTPLRStart(baselineIndex, dipIndex, fps=vidFps, changeThresh=0.2):
    diameterMM = df['diameter_mm'].values
    timestamp = df['timestamp'].values

    maxChange = changeThresh
    for i in range(baselineIndex, dipIndex):
        if not pd.isna(diameterMM[i]) and not pd.isna(diameterMM[i + 1]):
            change = abs(diameterMM[i + 1] - diameterMM[i])
            if change > maxChange:
                util.dprint(f"PLR start found at index {i} with diameter {diameterMM[i]} mm at time {timestamp[i]} s")
                return i

    util.dprint("PLR start not found within the specified range.")
    return -1

# time between onset and dip
def findDifference(onsetIndex, dipIndex, fps=vidFps):
    timeDiffSeconds = (dipIndex - onsetIndex) / fps
    util.dprint(f"Time difference between onset and dip: {timeDiffSeconds} seconds")
    return timeDiffSeconds

# find a new baseline to be 1.5s before the tplr start
def findNewBaselineIndex(tplrStartIndex, fps=vidFps, offsetThreshold=2):
    diameterMM = df['diameter_mm'].values
    timestamp = df['timestamp'].values

    onsetOffsetFrames = int(offsetThreshold * fps)
    onsetIndex = max(0, tplrStartIndex - onsetOffsetFrames)

    util.dprint(f"New Baseline onset approximated at index {onsetIndex} with diameter {diameterMM[onsetIndex]} mm at time {timestamp[onsetIndex]} s")
    return onsetIndex

# find baseline diameter to be average of all points in the 1.5s before tplr start
def findNewBaselineAvgDiameter(tplrStartIndex, fps=vidFps):
    diameterMM = df['diameter_mm'].values

    onsetOffsetFrames = int(1.5 * fps)
    startIndex = max(0, tplrStartIndex - onsetOffsetFrames)

    baselineValues = []
    for i in range(startIndex, tplrStartIndex):
        if not pd.isna(diameterMM[i]):
            baselineValues.append(diameterMM[i])

    if len(baselineValues) == 0:
        util.dprint("No valid baseline values found.")
        return None

    baselineDiameter = sum(baselineValues) / len(baselineValues)
    util.dprint(f"New Baseline diameter calculated as {baselineDiameter} mm from index {startIndex} to {tplrStartIndex - 1}")
    return baselineDiameter

# find the point where the pupil has fully recovered to be 6.7s after the dip
def findRecovery(baselineIndex, dipIndex, fps=vidFps, recoveryOffset=6.7):
    diameterMM = df['diameter_mm'].values
    timestamp = df['timestamp'].values

    recoveryOffsetFrames = int(recoveryOffset * fps)
    recoveryIndex = min(len(diameterMM) - 1, dipIndex + recoveryOffsetFrames)

    util.dprint(f"Recovery point approximated at index {recoveryIndex} with diameter {diameterMM[recoveryIndex]} mm at time {timestamp[recoveryIndex]} s")
    return recoveryIndex


# find end point as 35s after dip 
def findEndPoint(dipIndex, fps=vidFps, endOffset=35.0):
    diameterMM = df['diameter_mm'].values
    timestamp = df['timestamp'].values

    endOffsetFrames = int(endOffset * fps)
    endIndex = min(len(diameterMM) - 1, dipIndex + endOffsetFrames)

    util.dprint(f"End point approximated at index {endIndex} with diameter {diameterMM[endIndex]} mm at time {timestamp[endIndex]} s")
    return endIndex

# collect points from baseline to recovery to a new dataframe 
# also reset its timestamps from 0
def collectPLRSegment(baselineIndex, endPoint, plrStartIndex, fps=vidFps, ):
    diameterMM = df['diameter_mm'].values
    diameterPixels = df['diameter'].values
    timestamp = df['timestamp'].values

    plrData = {
        'timestamp': [],
        'diameter_mm': [],
        'diameter': []
    }

    for i in range(baselineIndex, endPoint + 1):
        plrData['timestamp'].append(timestamp[i] - timestamp[plrStartIndex])
        plrData['diameter_mm'].append(diameterMM[i])
        plrData['diameter'].append(diameterPixels[i])

    plrDF = pd.DataFrame(plrData)
    util.dprint(f"Collected PLR segment from index {baselineIndex} to {endPoint}, total {len(plrDF)} points.")
    util.dprint("First few rows of PLR segment dataframe:")
    print(plrDF.head())
    return plrDF

def findPoints(startingIndex):
    dipIndex = lowestDip(startingIndex)
    baselineIndex = findBaseline(dipIndex)
    TPLRStartIndex = findTPLRStart(baselineIndex, dipIndex)
    timeDiff = findDifference(TPLRStartIndex, dipIndex)

    baselineIndex = findNewBaselineIndex(TPLRStartIndex)
    recoveryIndex = findRecovery(baselineIndex, dipIndex)
    endPoint = findEndPoint(dipIndex)
    plrDF = collectPLRSegment(baselineIndex, endPoint, TPLRStartIndex)
    baselineDiameter = findNewBaselineAvgDiameter(TPLRStartIndex)
    return baselineDiameter, TPLRStartIndex, dipIndex, baselineIndex, plrDF

# find and display these metrics:
# - baseline avge diameter (mm)
# - transient PLR as the percentage of the lowest dip from baseline
# - constriction velocity as the rate of change from TPLR start to dip (mm/s)
# - peak constriction as diameter of lowest dip and percentage of dip to baseline 
# pipr bs to figure out later
def calculateMetrics(baselineDiameter, TPLRStartIndex, dipIndex, baselineIndex, plrDF):
    diameterMM = plrDF['diameter_mm'].values
    timestamp = plrDF['timestamp'].values

    lowestDipDiameter = diameterMM[dipIndex - baselineIndex]
    util.dprint(f"Lowest dip diameter: {lowestDipDiameter} mm")
    transientPLR = ((baselineDiameter - lowestDipDiameter) / baselineDiameter) * 100.0

    timeToDipSeconds = timestamp[dipIndex - baselineIndex] - timestamp[TPLRStartIndex - baselineIndex]
    constrictionVelocity = (baselineDiameter - lowestDipDiameter) / timeToDipSeconds if timeToDipSeconds > 0 else 0

    peakConstrictionPercentage = ((baselineDiameter - lowestDipDiameter) / baselineDiameter) * 100.0
    print(" ")
    util.dprint(f"Calculated Metrics:")
    util.dprint(f"Baseline Average Diameter: {baselineDiameter} mm")
    util.dprint(f"Transient PLR: {transientPLR} %")
    util.dprint(f"Constriction Velocity: {constrictionVelocity} mm/s")
    util.dprint(f"Peak Constriction Diameter: {lowestDipDiameter} mm ({peakConstrictionPercentage} % of baseline)")

    return {
        'baseline_diameter_mm': baselineDiameter,
        'transient_plr_percent': transientPLR,
        'constriction_velocity_mm_per_s': constrictionVelocity,
        'peak_constriction_diameter_mm': lowestDipDiameter,
        'peak_constriction_percent': peakConstrictionPercentage
    }


# start blue light stimuli at index 0
print(" ")
print("--------------------- BLUE LIGHT METRICS CALCULATION -----------------")
util.dprint("Calculating PLR metrics for blue light stimuli")
blueBaselineDiameter, blueTPLRStartIndex, blueDipIndex, blueBaselineIndex, bluePLRDF = findPoints(0)
blueMetrics = calculateMetrics(blueBaselineDiameter, blueTPLRStartIndex, blueDipIndex, blueBaselineIndex, bluePLRDF)
graph.plotResults(bluePLRDF, savePath=df1Path + "plrSegmentPlotBlue.png", showPlot=True, showMm=True, showConfidence=False, title="PLR Segment - Blue Light Stimuli")
util.dprint(f"Blue Light Stimuli: Baseline Diameter = {blueBaselineDiameter} mm, TPLR Start Index = {blueTPLRStartIndex}, Dip Index = {blueDipIndex}")

# start red light stimuli at approx 55s? (after blue stimuli ends + rest period)
print(" ")
print("--------------------- RED LIGHT METRICS CALCULATION -----------------")
util.dprint("Calculating PLR metrics for red light stimuli")
redStimuliStartIndex = int(55 * vidFps)
redBaselineDiameter, redTPLRStartIndex, redDipIndex, redBaselineIndex, redPLRDF = findPoints(redStimuliStartIndex)
redMetrics = calculateMetrics(redBaselineDiameter, redTPLRStartIndex, redDipIndex, redBaselineIndex, redPLRDF)
graph.plotResults(redPLRDF, savePath=df1Path + "plrSegmentPlotRed.png", showPlot=True, showMm=True, showConfidence=False, title="PLR Segment - Red Light Stimuli")
util.dprint(f"Red Light Stimuli: Baseline Diameter = {redBaselineDiameter} mm, TPLR Start Index = {redTPLRStartIndex}, Dip Index = {redDipIndex}")
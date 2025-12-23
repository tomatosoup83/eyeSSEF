# load a pupil csv data and then test them with the preprocessing scripts
import os
import pandas as pd
from main import dprint, confidenceThresh, pxToMm, plotResults
from scripts.preProcessing.secondPass import removeSusBio
from scripts.preProcessing.thirdPass import madFilter
from scripts.preProcessing.fourthPass import interpolateData
from scripts.preProcessing.fifthPass import averagePLRGraphs   
from scripts.preProcessing.firstPass import confidenceFilter

# load sample data
dprint("Loading sample pupil data for testing preprocessing scripts")
df1Path = "../videoImplement/data/PLR_Tuna_R_1280x720_60_1"
#df2Path = "../videoImplement/data/PLR_Tuna_R_1280x720_60_2/firstPass.csv"
df1 = pd.read_csv(df1Path + "/raw.csv")
#df2 = pd.read_csv(df2Path)

dprint("Initial data loaded:")
dprint(df1.head())

def doProcessing(df, fps=60, saveBeforeInterpolation=False, savePathBeforeInterpolation=df1Path + "/beforeInterpolation.csv"):
    # first pass
    df = confidenceFilter(df)
    dprint("After first pass (confidenceFilter):")
    dprint(df.head())

    # second pass
    df = removeSusBio(df, fps)
    dprint("After second pass (removeSusBio):")
    dprint(df.head())

    # third pass
    df = madFilter(df)
    dprint("After third pass (madFilter):")
    dprint(df.head())

    # save before interpolation if needed
    if saveBeforeInterpolation:
        dfNoInterpolation = df.copy()
        df.to_csv(savePathBeforeInterpolation, index=False)
        dprint(f"Data before interpolation saved to '{savePathBeforeInterpolation}'")

        # percentage of NaNs before interpolation
        totalPoints = len(dfNoInterpolation)
        badPoints = dfNoInterpolation['is_bad_data'].sum()
        badPercentage = (badPoints / totalPoints) * 100.0
        

    # fourth pass
    df = interpolateData(df, fps)
    dprint("After fourth pass (interpolateData):")
    dprint(df.head())

    if saveBeforeInterpolation: 
        return df, dfNoInterpolation, totalPoints, badPoints, badPercentage
    else: 
        return df


dprint("Processing first dataset")
df1_processed = doProcessing(df1, fps=60)
# get stats before interpolation
#df1_processed, df1_beforeInterpolation, totalPoints, badPoints, badPercentage = doProcessing(df1, fps=60, saveBeforeInterpolation=True, savePathBeforeInterpolation=df1Path + "/beforeInterpolation.csv")
#dprint(f"Before interpolation - Total data points: {totalPoints}, Bad data points: {badPoints}, Bad percentage: {badPercentage:.2f}%")

# save to csv
csvPreprocessedPath = "data/" + os.path.basename(df1Path).split('.')[0] + "/processed.csv"
df1_processed.to_csv(csvPreprocessedPath, index=False)
dprint(f"Processed data saved to CSV at '{csvPreprocessedPath}'")

# plotting results
dataFolderPath = "data/" + os.path.basename(df1Path).split('.')[0]
plotResults(df1_processed, savePath=dataFolderPath + "/processedPlot.png", showPlot=True, showMm=True)

# plot non interpolated data for comparison
#dataFolderPath = "data/" + os.path.basename(df1Path).split('.')[0]
#plotResults(df1_beforeInterpolation, savePath=dataFolderPath + "/beforeInterpolationPlot.png", showPlot=True, showMm=True)

#dprint("Processing second dataset")
#df2_processed = doProcessing(df2, fps=30)

# averaging
#dprint("Averaging the two processed datasets")
#averaged_df = averagePLRGraphs(df1_processed, df2_processed)
#dprint("After fifth pass (averagePLRGraphs):")
#dprint(averaged_df.head())
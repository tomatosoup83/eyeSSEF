from main import dprint, plotResults
import pandas as pd

csvPath = "./data/PLR_Tuna_R_1280x720_60_2/processed.csv"

# load to dataframe
df = pd.read_csv(csvPath)
plotResults(df, savePath="./data/PLR_Tuna_R_1280x720_60_2/plot_before_idkanymore.png", showPlot=True, showMm=True)
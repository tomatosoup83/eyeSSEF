# sixth pass
# Use a 3-point moving average to smooth the graph out (basically remove value at x with the average of values at x-1, x and x +1 

import pandas as pd
from main import dprint

def rollingAverage(dataframe):
    dprint("Starting sixth pass preprocessing...")
    smoothedDiameters = []
    smoothedDiameters_mm = []
    diameters = dataframe['diameter'].tolist()
    diameters_mm = dataframe['diameter_mm'].tolist()
    totalPoints = len(diameters)

    for i in range(totalPoints):
        if i == 0:
            avg = (diameters[i] + diameters[i + 1]) / 2
            avg_mm = (diameters_mm[i] + diameters_mm[i + 1]) / 2
        elif i == totalPoints - 1:
            avg = (diameters[i - 1] + diameters[i]) / 2
            avg_mm = (diameters_mm[i - 1] + diameters_mm[i]) / 2
        else:
            avg = (diameters[i - 1] + diameters[i] + diameters[i + 1]) / 3
            avg_mm = (diameters_mm[i - 1] + diameters_mm[i] + diameters_mm[i + 1]) / 3
        smoothedDiameters.append(avg)
        smoothedDiameters_mm.append(avg_mm)
        dprint(f"Replacing diameter at frame {i} with smoothed value {avg} pixels ({avg_mm} mm)")

    dataframe['diameter'] = smoothedDiameters
    dataframe['diameter_mm'] = smoothedDiameters_mm
    dprint("Sixth pass preprocessing completed.")
    return dataframe
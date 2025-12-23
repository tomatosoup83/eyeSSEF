# fifth pass: average the 2 PLR graphs from the same eye of a person
import pandas as pd
import numpy as np
from main import dprint, pxToMm

def averagePLRGraphs(df1, df2):
    dprint("Fifth pass preprocessing: averaging two PLR graphs")
    if len(df1) != len(df2):
        dprint("Error: DataFrames have different lengths, cannot average")
        return None
    averaged_df = df1.copy()
    diameters1 = df1['diameter'].values
    diameters2 = df2['diameter'].values
    averaged_diameters = []
    for i in range(len(diameters1)):
        d1 = diameters1[i]
        d2 = diameters2[i]
        if np.isnan(d1) and np.isnan(d2):
            averaged_diameters.append(np.nan)
        elif np.isnan(d1):
            averaged_diameters.append(d2)
        elif np.isnan(d2):
            averaged_diameters.append(d1)
        else:
            averaged_diameters.append((d1 + d2) / 2.0)
    averaged_df['diameter'] = averaged_diameters
    return averaged_df
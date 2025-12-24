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
    diameters1_mm = df1['diameter_mm'].values
    diameters2_mm = df2['diameter_mm'].values
    averaged_diameters_mm = []
    for i in range(len(diameters1_mm)):
        d1 = diameters1_mm[i]
        d2 = diameters2_mm[i]
        if np.isnan(d1) and np.isnan(d2):
            averaged_diameters_mm.append(np.nan)
        elif np.isnan(d1):
            averaged_diameters_mm.append(d2)
        elif np.isnan(d2):
            averaged_diameters_mm.append(d1)
        else:
            averaged_diameters_mm.append((d1 + d2) / 2.0)
    averaged_df['diameter_mm'] = averaged_diameters_mm
    averaged_df['diameter'] = np.array(averaged_diameters_mm) * pxToMm
    return averaged_df
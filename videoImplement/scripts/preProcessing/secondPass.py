# second pass: check for impossible biology
# reject if difference between consecutive frames is too large
# i.e > 0.5 at 60fps 
#     > 1.0 at 30fps
# if difference between frame n and frame n+1 is too large, set frame n+1 to NaN

# also check and remove if pupil diameter is above 9mm and below 2mm
import pandas as pd
import numpy as np
from main import dprint, confidenceThresh

def removeSusBio(df, fps=60):
    dprint("Second pass preprocessing: removing biologically implausible changes")

    # remove based on absolute diameter limits
    diameters = df['diameter_mm'].values
    pixelsDiamters = df['diameter'].values
    for i in range(len(diameters)):
        if not np.isnan(diameters[i]):
            if diameters[i] < 2.0 or diameters[i] > 9.0:
                dprint(f"Frame {i}: diameter {diameters[i]}mm is outside biological limits (2mm-9mm). Setting to NaN.")
                diameters[i] = np.nan
                pixelsDiamters[i] = np.nan
                # mark as bad data in dataframe
                df.at[i, 'is_bad_data'] = True

    # remove based on diameter difference
    maxChange = 0.5  # threshold based on fps
    diameters = df['diameter_mm'].values
    for i in range(1, len(diameters)):
        if i < len(diameters) - 1:  # ensure i+1 is within bounds
            if not np.isnan(diameters[i]) and not np.isnan(diameters[i+1]):
                if abs(diameters[i] - diameters[i+1]) > maxChange:
                    dprint(f"Frame {i}: diameter change {abs(diameters[i] - diameters[i+1])} exceeds max change {maxChange}. Setting to NaN.")
                    diameters[i] = np.nan
                    pixelsDiamters[i] = np.nan
                    # mark as bad data in dataframe
                    df.at[i, 'is_bad_data'] = True
    df['diameter_mm'] = diameters
    df['diameter'] = pixelsDiamters
    return df
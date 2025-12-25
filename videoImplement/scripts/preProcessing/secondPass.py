# second pass: check for impossible biology
# reject if difference between consecutive frames is too large
# i.e > 0.5 at 60fps 
#     > 1.0 at 30fps
# if difference between frame n and frame n+1 is too large, set frame n+1 to NaN

# also check and remove if pupil diameter is above 9mm and below 2mm
import pandas as pd
import numpy as np
from main import dprint, confidenceThresh

def removeSusBio(df, fps):
    dprint("Second pass preprocessing: removing biologically implausible changes")

    # remove based on absolute diameter limits
    diameters = df['diameter_mm'].values
    pixelsDiameters = df['diameter'].values
    for i in range(len(diameters)):
        if not np.isnan(diameters[i]):
            if diameters[i] < 2.0 or diameters[i] > 9.0:
                dprint(f"Frame {i}: diameter {diameters[i]}mm is outside biological limits (2mm-9mm). Setting to NaN.")
                diameters[i] = np.nan
                pixelsDiameters[i] = np.nan
                # mark as bad data in dataframe
                df.at[i, 'is_bad_data'] = True

    # remove based on diameter difference
    maxChange = 0.5 * (60 / fps) # threshold based on fps
    orig = df['diameter_mm'].values.copy()
    diameters = orig.copy()
    #for i in range(1, len(diameters)):
    #        if not np.isnan(orig[i]) and not np.isnan(orig[i-1]):
    #            if abs(orig[i] - orig[i-1]) > maxChange:
    #                dprint(f"Frame {i}: diameter change {abs(orig[i] - orig[i-1])} exceeds max change {maxChange}. Setting to NaN.")
    #                diameters[i] = np.nan
    #                pixelsDiamters[i] = np.nan
    #                # mark as bad data in dataframe
    #                df.at[i, 'is_bad_data'] = True

    for i in range(1, len(diameters) - 1): #1 -> n - 2
        if (not np.isnan(diameters[i]) and
            not np.isnan(diameters[i - 1]) and
            not np.isnan(diameters[i + 1])):

            change_from_prev = abs(diameters[i] - diameters[i - 1])
            change_from_next = abs(diameters[i] - diameters[i + 1])

            #if current frame is an outlier compared to its neighbours
            if change_from_prev > maxChange and change_from_next > maxChange:
                #current frame is sus
                dprint(f"Frame {i} is outlier, diameter change w.r.t neighbours exceeds max change")
                diameters[i] = np.nan
                pixelDiameters[i] = np.nan
                #mark as bad data in dataframe
                df.at[i, 'is_bad_data'] = True
            elif change_from_prev > maxChange and change_from_next <= maxChange:
                #previous frame might be the outlier
                if i > 1 and not np.isnan(diameters[i - 2]):
                    change_prev_to_prev2 = abs(diameters[i - 1] - diameters[i - 2])
                    if change_prev_to_prev2 > maxChange
                        dprint(f"Frame {i - 1} is outlier, diameter change w.r.t neighbours exceeds max change")
                        diameters[i - 1] = np.nan
                        pixel_diameters[i - 1] = np.nan
                        df.at[i - 1, 'is_bad_data'] = True
                
    df['diameter_mm'] = diameters
    df['diameter'] = pixelsDiamters
    return df

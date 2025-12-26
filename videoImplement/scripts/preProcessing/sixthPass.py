# sixth pass
# use savitzky-golay filter 

import numpy as np
import pandas as pd
from main import dprint
from scipy.signal import savgol_filter

"""
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
"""


def savgolSmoothing(dataframe, fps=60):

    n_points = len(dataframe)
    diameters = dataframe['diameter'].values.copy()
    diameters_mm = dataframe['diameter_mm'].values.copy()

    #handle nan bc savgol cant (safety feature, all nan shld alr be taken care of during the 4th pass)
    if np.any(np.isnan(diameters)):
        diameters = pd.Series(diameters).interpolate(method = 'linear', limit_direction = 'both').values
    if np.any(np.isnan(diameters_mm)):
        diameters_mm = pd.Series(diameters_mm).interpolate(method = 'linear', limit_direction = 'both').values

    #calc signal properties
    signad_std = np.std(diameters_mm)
    signal_range = np.max(diameters_mm) - np.min(diameters_mm)

    #adaptive window size based on fps and signal properties
    target_window_ms = 150 
    window_frames = int(target_window_ms / (1000 / fps))

    #window size must be odd
    if window_frames % 2 == 0:
        window_frames += 1

    #adjust based on signal quality
    if signal_std > 0.5: #noisy bad
        window_frames = min(window_frames + 2, 11) #larger window -> more smoothing
        polyorder = 2 #lower order (2 = quadratic) to prevent overfitting bad data
        dprint(f"Noisy signal, using window = {window_frames}, polyorder/power of the curve = {polyorder}")
    else: #clean signal good
        window_frames = max(5, window_frames) #smaller window -> better preserve peaks and troughs
        polyorder = 3 #cubic
        dprint(f"Clean signal, using window = {window_frames}, polyorder/power of the curve = {polyorder}")

    if window_frames > n_points:
        window_frames = n_points if n_points % 2 == 1 else n_points - 1
        window_frames = max(3, window_frames)

    if window_frames < 5:
        window_frames = 5

    if polyorder >= window_frames:
        polyorder = window_frames - 1

    dprint(f"Adaptive parameters: window = {window_frames}, polyorder = {polyorder}")

    #apply smoothing using the library
    smoothed = savgol_filter(diameters, window_length = window_frames, polyorder = polyorder, mode = 'interp')
    smoothed_mm = savgol_filter(diameters_mm, window_length = window_frames, polyorder = polyorder, mode = 'interp')

    nan_mask = np.isnan(diameters)
    smoothed[nan_mask] = np.nan
    smoothed_mm[nan_mask] = np.nan

    dataframe['diameter'] = smoothed
    dataframe['diameter_mm'] = smoothed_mm

    return dataframe
    

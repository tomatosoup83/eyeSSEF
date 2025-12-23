# third filtering
# use a 5-point median absolute deviation filter to remove outliers
# for each point, get the two neighbors before and after
# calculate the median of these 5 points
# calculate the absolute deviation of each point from the median (each point - median)
# calculate the median absolute deviation (MAD) (median of the absolute deviations)
# scale the MAD by 1.4826 to estimate standard deviation
# then u take 3 * scaled MAD as threshold
# if the absolute deviation of the center point exceeds this threshold, set it to NaN

# edge cases: for the first two and last two points, just use available neighbors
import pandas as pd
import numpy as np
from main import dprint
#from scipy.interpolate import CubicSpline

def madFilter(df):
    dprint("Third pass preprocessing: applying median absolute deviation filter")
    diameters = df['diameter_mm'].values
    pixelsDiamters = df['diameter'].values
    n = len(diameters)
    for i in range(n):
        # determine the window of points to consider
        start = max(0, i - 2)
        end = min(n - 1, i + 2)
        window = diameters[start:end + 1]
        # remove NaNs from the window
        window = window[~np.isnan(window)]
        if len(window) < 3:
            continue  # not enough data to compute MAD
        median = np.median(window)
        abs_devs = np.abs(window - median)
        mad = np.median(abs_devs)
        if mad == 0:
            continue  # no variation in data
        scaled_mad = mad * 1.4826
        threshold = 3 * scaled_mad
        if not np.isnan(diameters[i]):
            abs_dev = abs(diameters[i] - median)
            if abs_dev > threshold:
                dprint(f"Frame {i}: diameter {diameters[i]} deviates from median {median} by {abs_dev}, exceeding threshold {threshold}. Setting to NaN.")
                diameters[i] = np.nan
                pixelsDiamters[i] = np.nan
                # mark as bad data in dataframe
                df.at[i, 'is_bad_data'] = True
    df['diameter_mm'] = diameters
    df['diameter'] = pixelsDiamters
    return df


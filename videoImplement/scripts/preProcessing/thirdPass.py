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

madMultiplier = 2.5

def madFilter(df):
    #we shld actively search for non nan neighbours instead of just using a fixed size window ig
    dprint("Third pass preprocessing: applying median absolute deviation filter")
    #orig_diameters = df['diameter_mm'].values.copy()
    #diameters = orig_diameters.copy()
    diameters = df['diameter_mm'].values
    pixelsDiamters = df['diameter'].values
    
    n = len(diameters)
    window_size = 5 #might change to 7
    neighbours_cnt = window_size // 2
    
    for i in range(n):
        if np.isnan(diameters[i]):
            continue # skip alr removed points
            
        # determine the window of points to consider
        #start = max(0, i - neighbours_cnt)
        #end = min(n - 1, i + neighbours_cnt)

        #collect window points iteratively
        window_values = []
        window_indices = []

        #add current pt
        window_values.append(diameters[i])
        window_indices.append(i)

        #search for neighbours before current pt
        found_before = 0
        offset = 1

        while found_before < neighbours_cnt and i - offset >= 0:
            if not np.isnan(diameters[i - offset]):
                window_values.append(diameters[i - offset])
                window_indices.append(i - offset)
                found_before += 1
            offset += 1
            if offset > 10: #idk limit search so we dont go too far
                break

        #search for neighbours after current pt
        found_after = 0
        offset = 1

        while found_after < neighbours_cnt and i + offset < n:
            if not np.isnan(diameters[i + offset]):
                window_values.append(diameters[i + offset])
                window_indices.append(i + offset)
                found_after += 1
            offset += 1
            if offset > 10: 
                break

        if len(window_values) < 4: #raise the threshold
            continue

        #calc median
        window_median = np.median(window_values)
        abs_devs = [abs(val - window_median) for val in window_values]
        mad = np.median(abs_devs)

        if mad == 0:
            continue #no variation

        #scale MAD to estimate SD
        scaled_mad = mad * 1.4826
        threshold = 3 * scaled_mad

        cur_deviation = abs(window_values[0] - window_median)

        immediate_neighbours = []
        if i > 0 and not np.isnan(diameters[i - 1]):
            immediate_neighbours.append(diameters[i - 1])
        if i < n - 1 and not np.isnan(diameters[i + 1]):
            immediate_neighbours.append(diameters[i + 1])

        is_isolated_spike = False
        if len(immediate_neighbours) >= 1:
            #check if current pt is very different from its immediate neighbours
            avg_neighbour = np.mean(immediate_neighbours)
            if abs(diameters[i] - avg_neighbour) > threshold:
                is_isolated_spike = True

        #If current point is an outlier AND looks like an isolated spike
        if cur_deviation > threshold or is_isolated_spike:
            dprint(f"Frame {i}: diameter {diameters[i]} deviates from median {window_median} by {cur_deviation}, exceeding threshold {threshold}. Setting to NaN.")
            diameters[i] = np.nan
            pixelsDiameters[i] = np.nan
            df.at[i, 'is_bad_data'] = True

        #
        #if len(window) < 3:
            #continue  # not enough data to compute MAD
        #median = np.median(window)
        #abs_devs = np.abs(window - median)
        #mad = np.median(abs_devs)
        #if mad == 0:
            #continue  # no variation in data
       # scaled_mad = mad * 1.4826
        #threshold = 3 * scaled_mad
        #if not np.isnan(diameters[i]):
            #abs_dev = abs(diameters[i] - median)
            #if abs_dev > threshold:
                #dprint(f"Frame {i}: diameter {diameters[i]} deviates from median {median} by {abs_dev}, exceeding threshold {threshold}. Setting to NaN.")
                #diameters[i] = np.nan
                #pixelsDiamters[i] = np.nan
                # mark as bad data in dataframe
                #df.at[i, 'is_bad_data'] = True
    df['diameter_mm'] = diameters
    df['diameter'] = pixelsDiamters
    return df


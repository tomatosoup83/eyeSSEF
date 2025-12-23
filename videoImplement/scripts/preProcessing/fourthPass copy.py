# interpolate
# For gaps <100ms, use linear interpolation, for gaps <400ms, use cubic spline interpolation on 4 nearest neighbours 
import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline
from main import dprint, pxToMm

# seconds per frame = 1 / fps

def interpolateData(df, fps=60):
    dprint("Fourth pass preprocessing: interpolating missing data points")
    diameters = df['diameter_mm'].values
    pixelsDiamters = df['diameter'].values
    n = len(diameters)
    # find the frame threshold by fps
    # example: at 60fps, its 0.1 * 60 frames per second -> 6 frames for 100ms
    maxLinearGap = int(0.1 * fps)  # 100ms gap
    maxCubicGap = int(0.4 * fps)   # 400ms gap
    
    # calculate local median for outlier detection
    # use a sliding window to get robust baseline
    def is_outlier(value, idx, window_size=int(fps)):
        """Check if value is an outlier compared to local context"""
        if np.isnan(value):
            return True
        # get context window around the point
        start_idx = max(0, idx - window_size)
        end_idx = min(n, idx + window_size)
        context_values = diameters[start_idx:end_idx]
        valid_values = context_values[~np.isnan(context_values)]
        
        if len(valid_values) < 5:
            return False  # not enough data to judge
        
        median = np.median(valid_values)
        mad = np.median(np.abs(valid_values - median))  # median absolute deviation
        
        # use MAD-based threshold (more robust than std)
        # 3 * MAD threshold is roughly equivalent to 3 std deviations
        threshold = 3 * (1.4826 * mad)  # 1.4826 converts MAD to std equivalent
        
        if abs(value - median) > threshold:
            dprint(f"Outlier detected at frame {idx}: value={value:.2f}, median={median:.2f}, threshold={threshold:.2f}")
            return True
        return False

    i = 0
    while i < n:
        if np.isnan(diameters[i]):
            # i is the first NaN in a gap
            start = i
            # find the end of the gap
            # move i forward until non-NaN
            while i < n and np.isnan(diameters[i]):
                i += 1
            # get the end index of the gap
            end = i - 1
            gapSize = end - start + 1

            if gapSize <= maxLinearGap:
                # linear interpolation
                dprint(f"Frames {start} to {end}: performing linear interpolation for gap of size {gapSize}")
                x0 = start - 1
                x1 = end + 1
                if x0 >= 0 and x1 < n:
                    y0 = diameters[x0]
                    y1 = diameters[x1]
                    # validate boundary points are non-NaN and not outliers
                    if not np.isnan(y0) and not np.isnan(y1) and not is_outlier(y0, x0) and not is_outlier(y1, x1):
                        for j in range(start, end + 1):
                            # linear interpolation formula
                            diameters[j] = y0 + (y1 - y0) * (j - x0) / (x1 - x0)
                    else:
                        dprint(f"Skipping interpolation: boundary points invalid (y0={y0}, y1={y1})")
            elif gapSize <= maxCubicGap:
                # cubic spline interpolation
                dprint(f"Frames {start} to {end}: performing cubic spline interpolation for gap of size {gapSize}")
                x_points = []
                y_points = []
                # get up to 2 points before the gap
                for k in range(start - 2, start):
                    if k >= 0 and not np.isnan(diameters[k]) and not is_outlier(diameters[k], k):
                        x_points.append(k)
                        y_points.append(diameters[k])
                # get up to 2 points after the gap
                for k in range(end + 1, end + 3):
                    if k < n and not np.isnan(diameters[k]) and not is_outlier(diameters[k], k):
                        x_points.append(k)
                        y_points.append(diameters[k])
                if len(x_points) >= 4:
                    cs = CubicSpline(x_points, y_points)
                    for j in range(start, end + 1):
                        diameters[j] = cs(j)
                else:
                    dprint(f"Skipping cubic spline: insufficient valid boundary points ({len(x_points)} < 4)")
        else:
            i += 1

    df['diameter_mm'] = diameters
    return df
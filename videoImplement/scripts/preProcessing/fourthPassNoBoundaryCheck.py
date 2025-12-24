# interpolate
# For gaps <100ms, use linear interpolation, for gaps <400ms, use cubic spline interpolation on 4 nearest neighbours 
import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline
from main import dprint, pxToMm

# seconds per frame = 1 / fps

def _interpolateColumn(data, fps=60, column_name="diameter"):
    """Helper function to interpolate a single data column."""
    values = data.copy()
    n = len(values)
    # find the frame threshold by fps
    # example: at 60fps, its 0.1 * 60 frames per second -> 6 frames for 100ms
    maxLinearGap = int(0.1 * fps)  # 100ms gap
    maxCubicGap = int(0.4 * fps)   # 400ms gap
    i = 0
    while i < n:
        if np.isnan(values[i]):
            # i is the first NaN in a gap
            start = i
            # find the end of the gap
            # move i forward until non-NaN
            while i < n and np.isnan(values[i]):
                i += 1
            # get the end index of the gap
            end = i - 1
            gapSize = end - start + 1

            if gapSize <= maxLinearGap:
                # linear interpolation
                dprint(f"Frames {start} to {end}: performing linear interpolation for gap of size {gapSize} ({column_name})")
                x0 = start - 1
                x1 = end + 1
                if x0 >= 0 and x1 < n:
                    y0 = values[x0]
                    y1 = values[x1]
                    for j in range(start, end + 1):
                        values[j] = y0 + (y1 - y0) * (j - x0) / (x1 - x0)
            elif gapSize <= maxCubicGap:
                # cubic spline interpolation
                dprint(f"Frames {start} to {end}: performing cubic spline interpolation for gap of size {gapSize} ({column_name})")
                x_points = []
                y_points = []
                # get up to 2 points before the gap
                for k in range(start - 2, start):
                    if k >= 0 and not np.isnan(values[k]):
                        x_points.append(k)
                        y_points.append(values[k])
                # get up to 2 points after the gap
                for k in range(end + 1, end + 3):
                    if k < n and not np.isnan(values[k]):
                        x_points.append(k)
                        y_points.append(values[k])
                if len(x_points) >= 4:
                    cs = CubicSpline(x_points, y_points)
                    for j in range(start, end + 1):
                        values[j] = cs(j)
                else:
                    dprint(f"Skipping cubic spline: insufficient valid boundary points ({len(x_points)} < 4) ({column_name})")
        else:
            i += 1
    return values

def interpolateData(df, fps=60):
    dprint("Fourth pass preprocessing: interpolating missing data points")
    # Interpolate both diameter columns
    df['diameter_mm'] = _interpolateColumn(df['diameter_mm'].values, fps, "diameter_mm")
    df['diameter'] = _interpolateColumn(df['diameter'].values, fps, "diameter")
    return df
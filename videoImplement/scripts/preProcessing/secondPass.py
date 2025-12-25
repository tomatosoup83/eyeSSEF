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

    n = len(diameters)
    i = 1
    while i < n:
        if not np.isnan(diameters[i]) and not np.isnan(diameters[i - 1]):
            change = abs(diameters[i] - diameters[i - 1])

            if change > maxChange:
                #round a rapid change -> sus -> check if its part of a blink pattern 
                blink_start = i - 1
                blink_end = i

                #try to go backwards to find start of blink
                j = blink_start - 1
                while j >= 0 and not np.isnan(diameters[j]):
                    if j > 0 and not np.isnan(diameters[j - 1]):
                        if abs(diameters[j] - diameters[j - 1]) > maxChange:
                            blink_start = j
                            j -= 1
                        else:
                            break
                    else:
                        break

                #try to go forward to find end of blink
                j = blink_end + 1
                while j < n and not np.isnan(diameters[j]):
                    if j < n-1 and not np.isnan(diameters[j + 1]):
                        if abs(diameters[j] - diameters[j + 1]) > maxChange:
                            blink_end = j
                            j += 1 
                        else:
                            break
                    else:
                        break

                blink_len = blink_end - blink_start + 1

                #check if looks like a blink (v-shape or flipped v-shape wtv)
                if blink_len >= 3 and blink_len <= int(fps * 0.5) #acc to stein blinks r usually below <200ms but can go up to 500ms, so i just a 500ms threshold here
                    #extract blink segment
                    segment = diameters[blink_start:blink_end+1]

                    #check shape (using local min)
                    if len(segment) >= 3:
                        min_idx = np.argmin(segment)

                        #valid v shape if minimum is not at edges
                        if 0 < min_idx < len(segment) - 1:
                            amplitude = max(segment[0], segment[-1]) - segment[min_idx]
                            if amplitude > 0.5 * (fps / 60):
                                dprint(f"Frames {blink_start}-{blink_end}: Detected blink")

                                #mark blink frames as bad
                                for k in range(blink_start, blink_end + 1):
                                    diameters[k] = np.nan
                                    pixelDiameters[k] = np.nan
                                    df.at[k, 'is_bad_data'] = True

                                i = blink_end + 1 #skip past the blink
                                continue
        
                #if not a blink, just mark the rapid change as noise = bad
                dprint(f"Frame {i}: change {change} exceeds max change {maxChange}")
                diameters[i] = np.nan
                pixelDiameters[i] = np.nan
                df.at[i, 'is_bad_data'] = True

        i += 1
        
                
    df['diameter_mm'] = diameters
    df['diameter'] = pixelsDiamters
    return df

import numpy as np
from scipy.signal import hann
from scipy.ndimage import convolve1d
from scipy.interpolate import CubicSpline

def reconstruct_pupil_size(pupil, time=None, smooth_win=11, onset_thresh=-5, reversal_thresh=5, margin=10, dt=1):
    """
    Reconstructs pupil size during blinks using the algorithm described by Mathôt.
    
    Parameters:
    - pupil: np.array of pupil sizes (arbitrary units)
    - time: np.array of time points (in ms); if None, assumes np.arange(len(pupil)) * dt
    - smooth_win: int, size of Hanning window in samples (e.g., 11 for 11 ms at 1000 Hz)
    - onset_thresh: float, negative velocity threshold for blink onset
    - reversal_thresh: float, positive velocity threshold for blink reversal
    - margin: float, time margin in ms to add/subtract from onset/offset
    - dt: float, time step in ms (if time is None)
    
    Returns:
    - reconstructed: np.array of reconstructed pupil sizes
    - blinks: list of (start_idx, end_idx) for detected blinks
    
    Explanation:
    1. Smooth the pupil signal using a Hanning window average.
    2. Compute velocity as the difference of the smoothed signal divided by dt.
    3. Detect blinks by scanning for sequences: onset (vel drops below onset_thresh), 
       reversal (vel exceeds reversal_thresh), offset (vel drops back to <=0).
    4. Adjust onset/offset with margin.
    5. For each blink, select four symmetric points (t1, t2, t3, t4) from original signal.
    6. Fit a cubic spline to these points and replace the blink period (t2 to t3) with interpolated values.
    
    Note: Thresholds and window size should be tuned to your data. Assumes uniform sampling.
    Velocity units depend on pupil units and dt; adjust thresholds accordingly.
    """
    if time is None:
        time = np.arange(len(pupil)) * dt
    else:
        dt = np.mean(np.diff(time))  # Assume uniform
    
    # Step 1: Smooth the signal with Hanning window
    win = hann(smooth_win)
    win /= win.sum()  # Normalize for average
    smoothed = convolve1d(pupil, win, mode='nearest')  # Use 'nearest' to handle edges
    
    # Step 2: Compute velocity (rate of change)
    vel = np.zeros_like(smoothed)
    vel[1:] = np.diff(smoothed) / dt
    
    # Step 3: Detect blinks using velocity thresholds
    blinks = []
    i = 0
    while i < len(vel) - 1:
        # Find onset: where vel crosses below onset_thresh
        if vel[i] >= onset_thresh and vel[i + 1] < onset_thresh:
            onset_time = time[i + 1]
            # Find reversal: next where vel crosses above reversal_thresh
            j = i + 1
            while j < len(vel) - 1 and not (vel[j] <= reversal_thresh and vel[j + 1] > reversal_thresh):
                j += 1
            if j >= len(vel) - 1:
                break
            reversal_time = time[j + 1]
            # Find offset: after reversal, where vel drops to <=0
            k = j + 1
            while k < len(vel) - 1 and not (vel[k] > 0 and vel[k + 1] <= 0):
                k += 1
            if k >= len(vel) - 1:
                break
            offset_time = time[k + 1]
            
            # Adjust with margin
            onset_adj = onset_time - margin
            offset_adj = offset_time + margin
            
            # Get indices
            start_idx = np.searchsorted(time, onset_adj)
            end_idx = np.searchsorted(time, offset_adj)
            
            # Validate indices
            if start_idx < end_idx and end_idx < len(time):
                blinks.append((start_idx, end_idx))
                i = k + 1  # Skip to after this blink
            else:
                i += 1
        else:
            i += 1
    
    # Step 4: Reconstruct using cubic spline for each blink
    reconstructed = pupil.copy()
    for start, end in blinks:
        duration = time[end] - time[start]
        t2 = time[start]
        t3 = time[end]
        t1 = t2 - duration
        t4 = t3 + duration
        
        # Find indices, clamp to bounds
        i1 = max(0, np.searchsorted(time, t1))
        i4 = min(len(time) - 1, np.searchsorted(time, t4))
        
        # Use original pupil values
        ts = time[[i1, start, end, i4]]
        ps = pupil[[i1, start, end, i4]]
        
        # Cubic spline fit
        spline = CubicSpline(ts, ps)
        
        # Interpolate over blink period
        new_ts = time[start:end]
        new_ps = spline(new_ts)
        
        reconstructed[start:end] = new_ps
    
    return reconstructed, blinks
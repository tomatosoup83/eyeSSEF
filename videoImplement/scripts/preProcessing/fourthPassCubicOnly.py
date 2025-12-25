import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline, interp1d

def linear_interpolation(df, fps=60, max_gap_ms=400): #max 500ms
    df_interp = df.copy()
    frame_time_ms = 1000 / fps

    for col in ['diameter', 'diameter_mm']: #u change it to wtv your data is im not sure abt this one
        if col in df.column:
            values = df[col].values.copy()
            n = len(values)

            i = 0
            while i < n:
                if np.isnan(values[i]):
                    start = i

                    #find gap end
                    while i < n and np.isnan(values[i]):
                        i += 1
                    end = i - 1

                    gap_duration_ms = (end - start + 1) * frame_time_ms

                    #interpolate if gap < max_gap_ms
                    if gap_duration_ms <= max_gap_ms:
                        #find valid neighbours
                        before_idx = start - 1
                        after_idx = end + 1

                        if before_idx >= 0 and after_idx < n:
                            if not np.isnan(values[before_idx]) and not np.isnan(values[after_idx]):
                                before_val = values[before_idx]
                                after_val = values[after_idx]

                                for j in range(start, end + 1):
                                    t = (j - before_idx) / (after_idx - before_idx)
                                    values[j] = (1 - t) * before_val + t * after_val

                                print(f"Frames {start} - {end}: Linear interpolated {gap_duration_ms}")
                            else:
                                break
                        else:
                            break
                    else: 
                        break
                else:
                    i += 1

        df_temp = pd.DataFrame({col: values})
        df_temp[col] = df_temp[col].interpolate(method = 'linear', limit_direction = 'both')
        values = df_temp[col].values

        df_interp[col] = values

    return df_interp

def interpolateData(df):
    """
    Interpolate NaN values in diameter and diameter_mm columns 
    using cubic spline interpolation.
    
    Args:
        df: DataFrame with 'diameter' and 'diameter_mm' columns
    
    Returns:
        DataFrame with interpolated values
    """
    print("Interpolating NaN values using cubic spline (4 nearest neighbors)...\n")
    
    df_interpolated = df.copy()
    
    print("Processing 'diameter' column:")
    df_interpolated['diameter'] = interpolate_column_cubic_only(df['diameter'], 'diameter')
    
    print("\nProcessing 'diameter_mm' column:")
    df_interpolated['diameter_mm'] = interpolate_column_cubic_only(df['diameter_mm'], 'diameter_mm')
    
    return df_interpolated


if __name__ == "__main__":
    # Load the data
    csv_path = '../../data/PLR_Tuna_R_1280x720_60_2/beforeInterpolation.csv'
    print(f"Loading data from: {csv_path}\n")
    df = pd.read_csv(csv_path)
    
    # Show NaN counts before interpolation
    print("NaN counts before interpolation:")
    print(f"  diameter: {df['diameter'].isna().sum()}")
    print(f"  diameter_mm: {df['diameter_mm'].isna().sum()}\n")
    
    # Perform interpolation
    df_interpolated = interpolateData(df)
    
    # Show NaN counts after interpolation
    print(f"\nNaN counts after interpolation:")
    print(f"  diameter: {df_interpolated['diameter'].isna().sum()}")
    print(f"  diameter_mm: {df_interpolated['diameter_mm'].isna().sum()}\n")
    
    # Save the interpolated data
    output_path = '../../data/PLR_Tuna_R_1280x720_60_2/processed.csv'
    df_interpolated.to_csv(output_path, index=False)
    print(f"Interpolated data saved to: {output_path}")

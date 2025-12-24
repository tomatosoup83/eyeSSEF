import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline

def interpolate_column_cubic_only(data, column_name):
    """
    Interpolate NaN values in a column using cubic spline interpolation 
    with 4 nearest neighbors (2 before, 2 after the gap).
    
    Args:
        data: pandas Series with NaN values
        column_name: name of the column (for logging)
    
    Returns:
        interpolated pandas Series
    """
    values = data.copy()
    n = len(values)
    i = 0
    
    while i < n:
        if np.isnan(values[i]):
            # Found start of a NaN gap
            start = i
            
            # Find end of the gap
            while i < n and np.isnan(values[i]):
                i += 1
            end = i - 1
            gapSize = end - start + 1
            
            # Collect 4 valid points (expand search if needed)
            x_points = []
            y_points = []
            
            # Find 2 valid points before the gap
            before_count = 0
            k = start - 1
            while before_count < 2 and k >= 0:
                if not np.isnan(values[k]):
                    x_points.append(k)
                    y_points.append(values[k])
                    before_count += 1
                k -= 1
            
            # Find 2 valid points after the gap
            after_count = 0
            k = end + 1
            while after_count < 2 and k < n:
                if not np.isnan(values[k]):
                    x_points.append(k)
                    y_points.append(values[k])
                    after_count += 1
                k += 1
            
            # Only interpolate if we have 4 valid boundary points
            if len(x_points) >= 4:
                # Sort points by x index to ensure strictly increasing order
                sorted_pairs = sorted(zip(x_points, y_points))
                x_points = [p[0] for p in sorted_pairs]
                y_points = [p[1] for p in sorted_pairs]
                
                cs = CubicSpline(x_points, y_points)
                for j in range(start, end + 1):
                    values[j] = cs(j)
                print(f"  {column_name} - Frames {start} to {end}: cubic spline interpolation (gap size: {gapSize}, neighbors at: {x_points})")
            else:
                print(f"  {column_name} - Frames {start} to {end}: skipped (insufficient neighbors: {len(x_points)} < 4)")
        else:
            i += 1
    
    return values


def interpolate_dataframe(df):
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
    df_interpolated = interpolate_dataframe(df)
    
    # Show NaN counts after interpolation
    print(f"\nNaN counts after interpolation:")
    print(f"  diameter: {df_interpolated['diameter'].isna().sum()}")
    print(f"  diameter_mm: {df_interpolated['diameter_mm'].isna().sum()}\n")
    
    # Save the interpolated data
    output_path = '../../data/PLR_Tuna_R_1280x720_60_2/processed.csv'
    df_interpolated.to_csv(output_path, index=False)
    print(f"Interpolated data saved to: {output_path}")

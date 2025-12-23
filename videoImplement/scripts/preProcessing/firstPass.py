from main import dprint, confidenceThresh

def confidenceFilter(df):
    # set rows with confidence < 1 to NaN
    dprint(f"Preprocessing data: setting diameters with confidence < {confidenceThresh} to NaN")
    df.loc[df['confidence'] < confidenceThresh, 'diameter'] = float('nan')
    # do the same for diameter_mm
    df.loc[df['confidence'] < confidenceThresh, 'diameter_mm'] = float('nan')
    return df
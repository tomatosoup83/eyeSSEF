# check for bad trials based on percentage of NaN values
# if more than threshold percent of data is NaN, mark the whole trial as bad
import pandas as pd
from main import dprint, confidenceThresh

percentageThreshold = 30.0  # percent

def checkBadTrial(df):
    totalPoints = len(df)
    badPoints = df['is_bad_data'].sum()
    badPercentage = (badPoints / totalPoints) * 100.0
    dprint(f"Total data points: {totalPoints}, Bad data points: {badPoints}, Bad percentage: {badPercentage:.2f}%")
    if badPercentage > percentageThreshold:
        dprint(f"Trial marked as bad: {badPercentage:.2f}% of data points are bad (threshold: {percentageThreshold}%)")
        return True
    else:
        dprint(f"Trial marked as good: {badPercentage:.2f}% of data points are bad (threshold: {percentageThreshold}%)")
        return False
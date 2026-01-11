import pandas as pd
import numpy as np
from datetime import datetime

# Load the dataset
df = pd.read_csv('celebrity_marriages_wikidata.csv')

# --- DATA CLEANING ---
# Convert dates to datetime objects
df['Start_Date'] = pd.to_datetime(df['Start_Date'], errors='coerce')
df['End_Date'] = pd.to_datetime(df['End_Date'], errors='coerce')

# Calculate Duration
# For people still married, we calculate duration up to 'Today' for analysis, 
# but we mark them as "Censored" (stats term for 'event hasn't happened yet')
today = pd.to_datetime('today')
df['Observed_End_Date'] = df['End_Date'].fillna(today)
df['Duration_Days'] = (df['Observed_End_Date'] - df['Start_Date']).dt.days
df['Duration_Years'] = df['Duration_Days'] / 365.25

# Determine Status
# If End_Date is missing, they are "Still Married" (or data is missing)
df['Status'] = np.where(df['End_Date'].notnull(), 'Ended', 'Ongoing')

# --- PRELIMINARY INSIGHTS ---

# 1. Who married the most times?
most_married = df['Celebrity'].value_counts().head(5)

# 2. Shortest Marriages (that actually ended)
shortest = df[df['Status'] == 'Ended'].sort_values('Duration_Days').head(5)[['Celebrity', 'Spouse', 'Duration_Days', 'Start_Date']]

# 3. Average Duration of Ended Marriages
avg_duration = df[df['Status'] == 'Ended']['Duration_Years'].median()

# Display results
print("--- INSIGHTS REPORT ---")
print(f"Total Records: {len(df)}")
print(f"Median Duration of Ended Marriages: {avg_duration:.2f} years")
print("\nTop 5 Most Married Celebrities in Dataset:")
print(most_married)
print("\nTop 5 Shortest Marriages (Days):")
print(shortest.to_string(index=False))
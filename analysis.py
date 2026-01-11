import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv('celebrity_marriages_enriched.csv')

# --- 1. DATA CLEANING ---
date_cols = ['Start_Date', 'End_Date', 'Celebrity_Birth', 'Spouse_Birth']
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors='coerce')

df = df.dropna(subset=['Start_Date'])
today = pd.to_datetime('today')
df['Observed_End_Date'] = df['End_Date'].fillna(today)
df['Duration_Days'] = (df['Observed_End_Date'] - df['Start_Date']).dt.days
df['Duration_Years'] = df['Duration_Days'] / 365.25
df = df[df['Duration_Days'] > 0]

# Define Event (Divorce = 1)
def get_event_status(row):
    if pd.isnull(row['End_Date']): return 0
    cause = str(row['End_Cause']).lower()
    if 'death' in cause or 'widow' in cause: return 0 
    return 1

df['Event_Divorce'] = df.apply(get_event_status, axis=1)
df['Status_Label'] = df['Event_Divorce'].map({1: 'Divorced', 0: 'Ongoing/Widowed'})

# Calculate Features
df['Age_Gap'] = abs((df['Celebrity_Birth'] - df['Spouse_Birth']).dt.days / 365.25)
df['Fame_Gap_Raw'] = abs(df['Celebrity_Fame_Score'] - df['Spouse_Fame_Score'])
df['Spouse_Type'] = np.where(df['Spouse_Fame_Score'] > 20, 'Famous Spouse', 'Non-Famous Spouse')

# Remove Age Gap outliers (e.g. > 60 years or NaN) for cleaner plots
df_clean = df.dropna(subset=['Age_Gap'])
df_clean = df_clean[df_clean['Age_Gap'] < 60]

# --- 2. ANALYSIS ---

# Insight A: Age Gap Impact
# Bin the Age Gaps
bins = [0, 5, 10, 20, 100]
labels = ['0-5 Years', '5-10 Years', '10-20 Years', '20+ Years']
df_clean['Age_Gap_Bin'] = pd.cut(df_clean['Age_Gap'], bins=bins, labels=labels)

# Calculate Divorce Rate per Bin (Ratio of Divorced to Total in that bin)
age_gap_stats = df_clean.groupby('Age_Gap_Bin', observed=False).agg(
    Total_Marriages=('Status_Label', 'count'),
    Divorce_Rate=('Event_Divorce', 'mean'),
    Median_Duration=('Duration_Years', 'median')
).reset_index()

# Insight B: Fame Impact
fame_stats = df_clean.groupby('Spouse_Type').agg(
    Total_Marriages=('Status_Label', 'count'),
    Divorce_Rate=('Event_Divorce', 'mean'),
    Median_Duration=('Duration_Years', 'median')
).reset_index()

# --- 3. PLOTTING ---
plt.figure(figsize=(16, 10))

# Plot 1: Age Gap vs Divorce Rate (Bar Chart)
plt.subplot(2, 2, 1)
sns.barplot(data=age_gap_stats, x='Age_Gap_Bin', y='Divorce_Rate', palette='Reds')
plt.title('Divorce Rate by Age Difference', fontsize=14)
plt.ylabel('Divorce Rate (0.0 - 1.0)')
plt.xlabel('Age Gap Category')
plt.ylim(0, 1)

# Plot 2: Age Gap vs Duration (Box Plot for Divorced Couples Only)
# To see if large age gaps lead to *quicker* divorces
plt.subplot(2, 2, 2)
sns.boxplot(data=df_clean[df_clean['Event_Divorce']==1], x='Age_Gap_Bin', y='Duration_Years', palette='Blues')
plt.title('Duration of Marriages that Ended (by Age Gap)', fontsize=14)
plt.ylabel('Years until Divorce')

# Plot 3: Spouse Fame Type vs Duration (Violin Plot)
plt.subplot(2, 2, 3)
sns.violinplot(data=df_clean[df_clean['Event_Divorce']==1], x='Spouse_Type', y='Duration_Years', palette='Greens')
plt.title('Duration: Marrying Famous vs Non-Famous', fontsize=14)

# Plot 4: Scatter of Fame Gap vs Duration
plt.subplot(2, 2, 4)
sns.scatterplot(data=df_clean[df_clean['Event_Divorce']==1], x='Fame_Gap_Raw', y='Duration_Years', alpha=0.6)
plt.title('Fame Gap vs Duration (Scatter)', fontsize=14)
plt.xlabel('Difference in Fame Score')
plt.ylabel('Duration (Years)')

plt.tight_layout()
plt.savefig('celebrity_analysis_results.png')

# Print Text Summary
print("--- RESEARCH FINDINGS ---")
print("\n1. Impact of Age Gap:")
print(age_gap_stats)
print("\n2. Impact of Marrying a Famous Spouse:")
print(fame_stats)

# Correlation
corr = df_clean[df_clean['Event_Divorce']==1][['Duration_Years', 'Age_Gap', 'Fame_Gap_Raw']].corr()
print("\n3. Correlation Matrix (Divorced Only):")
print(corr)
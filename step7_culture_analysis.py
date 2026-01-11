import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from lifelines import KaplanMeierFitter

# --- 1. LOAD & DIAGNOSE ---
print("📂 Loading Data...")
df = pd.read_csv('celebrity_culture_profession.csv')

# DIAGNOSTIC: Print the actual counts found in the file
print("\n--- 🌍 TOP 15 COUNTRIES FOUND ---")
print(df['Country'].value_counts().head(15))
print("---------------------------------\n")

# Clean Data
df['Start_Date'] = pd.to_datetime(df['Start_Date'], errors='coerce')
df['End_Date'] = pd.to_datetime(df['End_Date'], errors='coerce')
df = df.dropna(subset=['Start_Date'])

today = pd.to_datetime('today')
df['Observed_End_Date'] = df['End_Date'].fillna(today)
df['Duration_Years'] = (df['Observed_End_Date'] - df['Start_Date']).dt.days / 365.25
df = df[df['Duration_Years'] > 0]

def get_status(row):
    if pd.isnull(row['End_Date']): return 0
    if 'death' in str(row['End_Cause']).lower(): return 0
    return 1
df['Event'] = df.apply(get_status, axis=1)

# --- 2. THE FIX: RELAXED FILTERING ---
# We look for partial matches to catch 'Republic of India' or 'India'
target_countries = ['United States', 'United Kingdom', 'India', 'France']
colors = {'United States': 'blue', 'United Kingdom': 'red', 'India': 'green', 'France': 'purple'}

plt.figure(figsize=(16, 8))

# Plot 1: Profession
plt.subplot(1, 2, 1)
df_job = df[df['Occupation'].astype(str).str.contains('actor|musician|singer', case=False)].copy()
df_job['Job_Group'] = np.where(df_job['Occupation'].str.contains('actor', case=False), 'Actor', 'Musician')

kmf = KaplanMeierFitter()
for job in ['Actor', 'Musician']:
    mask = df_job['Job_Group'] == job
    if mask.sum() > 10: # Lowered threshold
        kmf.fit(df_job[mask]['Duration_Years'], df_job[mask]['Event'], label=f"{job} (n={mask.sum()})")
        kmf.plot_survival_function(linewidth=3)
plt.title('Musicians vs. Actors', fontsize=14)
plt.grid(True, alpha=0.3)

# Plot 2: Culture (With Debugging)
plt.subplot(1, 2, 2)

for target in target_countries:
    # Flexible search: matches "United States of America" if target is "United States"
    mask = df['Country'].astype(str).str.contains(target, case=False, na=False)
    
    count = mask.sum()
    if count > 5: # DRAMATICALLY LOWERED THRESHOLD (From 50 to 5)
        # Grab the actual name used in the data for the label
        actual_name = df[mask]['Country'].iloc[0]
        kmf.fit(df[mask]['Duration_Years'], df[mask]['Event'], label=f"{actual_name} (n={count})")
        kmf.plot_survival_function(linewidth=3, color=colors.get(target, 'grey'))
    else:
        print(f"⚠️ Warning: '{target}' has only {count} records. Line hidden.")

plt.title('Culture: USA vs UK vs India vs France', fontsize=14)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('culture_profession_dashboard_v2.png')
print("\n✅ Dashboard Saved: culture_profession_dashboard_v2.png")
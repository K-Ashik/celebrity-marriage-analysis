import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from lifelines import KaplanMeierFitter
from sklearn.linear_model import LogisticRegression
from datetime import datetime

# --- CONFIGURATION ---
INPUT_FILE = "celebrity_marriages_enriched.csv"
OUTPUT_IMAGE = "celebrity_marriage_dashboard.png"

# Load Data
print(f"📂 Loading {INPUT_FILE}...")
df = pd.read_csv(INPUT_FILE)

# --- 1. DATA CLEANING & FEATURE ENGINEERING ---
print("⚙️  Processing data and engineering features...")

# Convert dates to datetime objects
date_cols = ['Start_Date', 'End_Date', 'Celebrity_Birth', 'Spouse_Birth']
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# Drop invalid rows (must have a start date)
df = df.dropna(subset=['Start_Date'])

# Calculate Duration
# If End_Date is missing, we assume the marriage is ongoing (use Today's date for calc)
today = pd.to_datetime('today')
df['Observed_End_Date'] = df['End_Date'].fillna(today)
df['Duration_Days'] = (df['Observed_End_Date'] - df['Start_Date']).dt.days
df['Duration_Years'] = df['Duration_Days'] / 365.25

# Filter out data errors (negative duration)
df = df[df['Duration_Days'] > 0]

# Define "Event" (Divorce = 1, Ongoing/Death = 0)
# In Survival Analysis, "Censored" means the event hasn't happened yet (or they died married).
def get_event_status(row):
    if pd.isnull(row['End_Date']):
        return 0 # Censored (Ongoing)
    
    cause = str(row['End_Cause']).lower()
    if 'death' in cause or 'widow' in cause:
        return 0 # Censored (Death is not a failed marriage)
    
    return 1 # Event (Divorce/Separation)

df['Event_Divorce'] = df.apply(get_event_status, axis=1)

# Calculate Risk Factors (Variables)
# 1. Age Gap
df['Age_Gap'] = abs((df['Celebrity_Birth'] - df['Spouse_Birth']).dt.days / 365.25).fillna(0)

# 2. Fame Gap & Spouse Type
df['Celebrity_Fame_Score'] = df['Celebrity_Fame_Score'].fillna(0)
df['Spouse_Fame_Score'] = df['Spouse_Fame_Score'].fillna(0)
df['Fame_Gap'] = abs(df['Celebrity_Fame_Score'] - df['Spouse_Fame_Score'])
df['Is_Famous_Spouse'] = (df['Spouse_Fame_Score'] > 20).astype(int)
df['Spouse_Type_Label'] = np.where(df['Is_Famous_Spouse'] == 1, 'Famous Spouse', 'Non-Famous')

# --- 2. SURVIVAL ANALYSIS (Kaplan-Meier) ---
print("📉 Running Kaplan-Meier Survival Analysis...")
kmf = KaplanMeierFitter()
kmf.fit(durations=df['Duration_Years'], event_observed=df['Event_Divorce'])

# --- 3. RISK MODELING (Logistic Regression) ---
print("🤖 Training Risk Model (Logistic Regression)...")
# We predict if a marriage fails in < 5 years (Short Marriage)
# Filter for meaningful data (either ended, or ongoing > 5 years)
model_data = df[ (df['Event_Divorce']==1) | (df['Duration_Years'] > 5) ].copy()
model_data['Target_Short_Marriage'] = (model_data['Duration_Years'] <= 5).astype(int)

X = model_data[['Age_Gap', 'Fame_Gap', 'Is_Famous_Spouse']]
y = model_data['Target_Short_Marriage']

model = LogisticRegression()
model.fit(X, y)

# Extract Coefficients (Risk Scores)
risk_factors = pd.DataFrame({
    'Factor': ['Age Difference', 'Fame Difference', 'Spouse Is Famous?'],
    'Risk_Score': model.coef_[0]
})

# --- 4. VISUALIZATION DASHBOARD ---
print("🎨 Generating Dashboard...")
plt.figure(figsize=(14, 10))
plt.suptitle('The Science of Celebrity Divorce', fontsize=20, weight='bold')

# Plot 1: Survival Curve
plt.subplot(2, 2, 1)
kmf.plot_survival_function(linewidth=3, color='#007acc')
plt.title('The "Hollywood Survival Curve"', fontsize=14)
plt.ylabel('Probability of Staying Married')
plt.xlabel('Years Married')
plt.grid(True, alpha=0.3)
plt.axvline(x=12, color='red', linestyle='--', alpha=0.6)
plt.text(12.5, 0.6, 'Median: 12 Years', color='red', fontsize=10)

# Plot 2: Risk Factors (Coefficients)
plt.subplot(2, 2, 2)
sns.barplot(data=risk_factors, x='Factor', y='Risk_Score', palette='RdYlGn_r')
plt.title('What Increases Divorce Risk?', fontsize=14)
plt.ylabel('Risk Impact (Higher = More Dangerous)')
plt.axhline(0, color='black', linewidth=1)

# Plot 3: Duration by Spouse Type
plt.subplot(2, 2, 3)
sns.boxplot(data=df[df['Event_Divorce']==1], x='Spouse_Type_Label', y='Duration_Years', palette='Pastel1')
plt.title('Duration: Marrying Famous vs. Non-Famous', fontsize=14)
plt.xlabel('')
plt.ylabel('Years until Divorce')

# Plot 4: Age Gap Scatter
plt.subplot(2, 2, 4)
sns.scatterplot(data=df[df['Event_Divorce']==1], x='Age_Gap', y='Duration_Years', alpha=0.5, size='Fame_Gap', sizes=(20, 200))
plt.title('Age Gap vs. Duration (Size = Fame Diff)', fontsize=14)
plt.xlabel('Age Difference (Years)')
plt.ylabel('Duration (Years)')
plt.xlim(0, 40)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig(OUTPUT_IMAGE)
print(f"✅ Dashboard saved to: {OUTPUT_IMAGE}")

# --- 5. PRINT STATS ---
print("\n" + "="*40)
print("       RESEARCH CONCLUSION")
print("="*40)
print(f"Median Celebrity Marriage Length: {kmf.median_survival_time_:.2f} Years")
print(f"Probability of lasting 10 Years:  {kmf.predict(10):.2%}")
print("-" * 40)
print("RISK FACTORS (Logistic Regression):")
print(risk_factors.to_string(index=False))
print("-" * 40)
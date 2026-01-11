import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from lifelines import KaplanMeierFitter, CoxPHFitter

# --- 1. LOAD & ENGINEER VARIABLES ---
print("🧠 Loading Psycho-Economic Data...")
df = pd.read_csv('celebrity_psycho_economics.csv')

# Convert Dates
cols = ['Start_Date', 'End_Date', 'Celebrity_Birth', 'Career_Start_Year']
for c in cols:
    df[c] = pd.to_datetime(df[c], errors='coerce')

df = df.dropna(subset=['Start_Date', 'Celebrity_Birth', 'Career_Start_Year'])

# Calculate Duration (The "Time" variable)
today = pd.to_datetime('today')
df['Observed_End_Date'] = df['End_Date'].fillna(today)
df['Duration_Years'] = (df['Observed_End_Date'] - df['Start_Date']).dt.days / 365.25
df = df[df['Duration_Years'] > 0]

# Define Event (1=Divorce, 0=Ongoing/Widowed)
def get_status(row):
    if pd.isnull(row['End_Date']): return 0
    if 'death' in str(row['End_Cause']).lower(): return 0
    return 1
df['Event'] = df.apply(get_status, axis=1)

# --- PSYCHOLOGICAL VARIABLE: CHILD STAR SYNDROME ---
# Calculate Age at Career Start
df['Age_At_Debut'] = (df['Career_Start_Year'] - df['Celebrity_Birth']).dt.days / 365.25

# Filter invalid data (e.g., negative ages)
df = df[(df['Age_At_Debut'] > 0) & (df['Age_At_Debut'] < 80)]

# Define "Child Star" (Started working before age 16)
df['Is_Child_Star'] = np.where(df['Age_At_Debut'] < 16, 'Child Star', 'Adult Debut')
df['Is_Child_Star_Binary'] = np.where(df['Age_At_Debut'] < 16, 1, 0)

# --- FAMILY VARIABLE: THE BABY ANCHOR ---
# Group children count for cleaner plotting
df['Children_Category'] = pd.cut(df['Children_Count'], bins=[-1, 0, 2, 20], labels=['No Kids', '1-2 Kids', '3+ Kids'])

# --- 2. MULTIVARIATE ANALYSIS (COX HAZARD MODEL) ---
print("⚙️ Running Cox Proportional Hazards Model...")

# We select the variables for the "Formula"
# This tells us the exact % risk increase/decrease for each factor
cox_data = df[['Duration_Years', 'Event', 'Is_Child_Star_Binary', 'Children_Count', 'Awards_Count']]

cph = CoxPHFitter()
cph.fit(cox_data, duration_col='Duration_Years', event_col='Event')

# --- 3. VISUALIZATION DASHBOARD ---
plt.figure(figsize=(16, 10))
plt.suptitle('Psycho-Economic Analysis of Celebrity Divorce', fontsize=20, weight='bold')

# PLOT 1: The Child Star Syndrome (Survival Curve)
plt.subplot(2, 2, 1)
kmf = KaplanMeierFitter()
for group in ['Child Star', 'Adult Debut']:
    mask = df['Is_Child_Star'] == group
    kmf.fit(df[mask]['Duration_Years'], df[mask]['Event'], label=group)
    kmf.plot_survival_function(linewidth=3)
plt.title('Do "Child Stars" Crash Faster?', fontsize=14)
plt.ylabel('Probability of Staying Married')
plt.grid(True, alpha=0.3)

# PLOT 2: The Baby Anchor (Survival Curve by Kids)
plt.subplot(2, 2, 2)
colors = {'No Kids': 'red', '1-2 Kids': 'orange', '3+ Kids': 'green'}
for group in ['No Kids', '1-2 Kids', '3+ Kids']:
    mask = df['Children_Category'] == group
    if mask.sum() > 0:
        kmf.fit(df[mask]['Duration_Years'], df[mask]['Event'], label=group)
        kmf.plot_survival_function(linewidth=2, color=colors[group])
plt.title('The "Baby Anchor": Do Kids Save Marriages?', fontsize=14)
plt.grid(True, alpha=0.3)

# PLOT 3: The Oscar Curse (Scatter)
# Does having more awards lead to shorter marriages?
plt.subplot(2, 2, 3)
sns.regplot(data=df[df['Event']==1], x='Awards_Count', y='Duration_Years', scatter_kws={'alpha':0.3}, line_kws={'color':'red'})
plt.title('The "Oscar Curse": Awards vs. Duration', fontsize=14)
plt.xlabel('Number of Major Awards Won')
plt.ylabel('Years until Divorce')

# PLOT 4: The Hazard Coefficients (The "Science" Result)
plt.subplot(2, 2, 4)
cph.plot()
plt.title('Risk Factors (Right = Higher Divorce Risk)', fontsize=14)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig('psycho_economic_dashboard.png')
print("✅ Dashboard saved: psycho_economic_dashboard.png")

# --- 4. PRINT SCIENTIFIC FINDINGS ---
print("\n" + "="*40)
print("     🧬 PSYCHO-ECONOMIC FINDINGS")
print("="*40)
print(cph.summary[['coef', 'exp(coef)', 'p']])
print("-" * 40)
print("INTERPRETATION:")
print(f"1. Child Stars Risk: {cph.params_['Is_Child_Star_Binary']:.2f} (Positive = Higher Risk)")
print(f"2. Kids Protection:  {cph.params_['Children_Count']:.2f} (Negative = Protective)")
print(f"3. Awards Risk:      {cph.params_['Awards_Count']:.2f}")
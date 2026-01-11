import requests
import pandas as pd
from tqdm import tqdm

# --- CONFIGURATION ---
url = "https://query.wikidata.org/sparql"

# --- THE "PSYCHO-ECONOMIC" QUERY ---
# Fetching: 
# 1. Start of Career (P2031) -> To calculate "Child Star" status
# 2. Number of Children (P1971 or count of P40) -> The "Baby Anchor"
# 3. Number of Awards (count of P166) -> The "Status/Economic" level
query = """
SELECT DISTINCT 
  ?celebrityLabel ?spouseLabel 
  ?start ?end ?endCauseLabel
  ?c_birth ?career_start
  (COUNT(DISTINCT ?child) AS ?child_count)
  (COUNT(DISTINCT ?award) AS ?award_count)
WHERE {
  # 1. Identify Famous Actors
  ?celebrity wdt:P31 wd:Q5;
             wdt:P106 wd:Q33999;
             wikibase:sitelinks ?sitelinks.
  FILTER(?sitelinks > 50) 
  
  # 2. Marriage Info
  ?celebrity p:P26 ?statement.
  ?statement ps:P26 ?spouse.
  
  OPTIONAL { ?statement pq:P580 ?start. }
  OPTIONAL { ?statement pq:P582 ?end. }
  OPTIONAL { ?statement pq:P1534 ?endCause. }
  
  # 3. Psychological Variable: Age & Career Start (Child Star Factor)
  OPTIONAL { ?celebrity wdt:P569 ?c_birth. }
  OPTIONAL { ?celebrity wdt:P2031 ?career_start. }
  
  # 4. Family Variable: Children (The "Anchor")
  OPTIONAL { ?celebrity wdt:P40 ?child. }
  
  # 5. Economic/Status Variable: Awards Won
  OPTIONAL { ?celebrity wdt:P166 ?award. }
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
GROUP BY ?celebrityLabel ?spouseLabel ?start ?end ?endCauseLabel ?c_birth ?career_start
LIMIT 3000
"""

print("🧠 Sending Psycho-Economic Query to Wikidata...")
print("(This query is complex and might take 10-15 seconds...)")

try:
    headers = {'User-Agent': 'CelebrityResearchBot/2.0'}
    r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
    
    if r.status_code == 200:
        data = r.json()
        results = []
        
        print(f"Parsing {len(data['results']['bindings'])} records...")
        
        for item in tqdm(data['results']['bindings']):
            def get_val(key): return item.get(key, {}).get('value', None)
            
            # Basic Info
            celebrity = get_val('celebrityLabel')
            spouse = get_val('spouseLabel')
            
            # Dates
            start_date = get_val('start')
            end_date = get_val('end')
            if start_date: start_date = start_date.split('T')[0]
            if end_date: end_date = end_date.split('T')[0]
            
            # Crucial Fix: Capture End Cause
            end_cause = get_val('endCauseLabel')

            # Psychological Data (Child Star)
            birth_date = get_val('c_birth')
            career_start = get_val('career_start')
            if birth_date: birth_date = birth_date.split('T')[0]
            if career_start: career_start = career_start.split('T')[0]
            
            # Economic/Family Data
            children = get_val('child_count')
            awards = get_val('award_count')

            results.append({
                "Celebrity": celebrity,
                "Spouse": spouse,
                "Start_Date": start_date,
                "End_Date": end_date,
                "End_Cause": end_cause,  # <--- FIXED: Now saving the cause!
                "Celebrity_Birth": birth_date,
                "Career_Start_Year": career_start,
                "Children_Count": children,
                "Awards_Count": awards
            })

        # Save to new dataset
        df = pd.DataFrame(results)
        
        # CLEANUP: Fill NaNs for counts with 0
        df['Children_Count'] = df['Children_Count'].fillna(0).astype(int)
        df['Awards_Count'] = df['Awards_Count'].fillna(0).astype(int)
        
        filename = "celebrity_psycho_economics.csv"
        df.to_csv(filename, index=False)
        
        print("-" * 30)
        print(f"✅ Success! Created '{filename}' (Now includes End_Cause)")
        print("-" * 30)
        print(df.head())
        
    else:
        print(f"❌ Wikidata Error: {r.status_code}")

except Exception as e:
    print(f"❌ Script Error: {e}")
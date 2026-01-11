import requests
import pandas as pd
from tqdm import tqdm

# --- CONFIGURATION ---
url = "https://query.wikidata.org/sparql"

# --- THE UPGRADED QUERY ---
# Fetching: Names, Marriage Dates, Birth Dates (for Age Gap), and Sitelinks (for Fame Gap)
query = """
SELECT DISTINCT 
  ?celebrityLabel ?spouseLabel 
  ?start ?end ?endCauseLabel
  ?c_birth ?s_birth
  ?c_fame ?s_fame
WHERE {
  # 1. Find Actors with > 30 sitelinks (The "Famous" ones)
  ?celebrity wdt:P31 wd:Q5;
             wdt:P106 wd:Q33999;
             wikibase:sitelinks ?c_fame.
  FILTER(?c_fame > 30)
  
  # 2. Get Spouse Info
  ?celebrity p:P26 ?statement.
  ?statement ps:P26 ?spouse.
  
  # 3. Get Spouse Fame (Optional)
  OPTIONAL { ?spouse wikibase:sitelinks ?s_fame. }
  
  # 4. Get Dates (Marriage)
  OPTIONAL { ?statement pq:P580 ?start. }
  OPTIONAL { ?statement pq:P582 ?end. }
  OPTIONAL { ?statement pq:P1534 ?endCause. }
  
  # 5. Get Birth Dates (To calculate Age at Marriage)
  OPTIONAL { ?celebrity wdt:P569 ?c_birth. }
  OPTIONAL { ?spouse wdt:P569 ?s_birth. }
  
  # Label service for names
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
LIMIT 3000
"""

print("🚀 Sending Advanced Query to Wikidata (JSON Mode)...")

try:
    # REQUEST JSON (More robust than CSV)
    headers = {'User-Agent': 'CelebrityResearchBot/1.0'}
    r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
    
    if r.status_code == 200:
        data = r.json()
        results = []
        
        print("Parsing data...")
        # Loop through the JSON results safely
        for item in tqdm(data['results']['bindings']):
            # Helper function to grab value if exists
            def get_val(key):
                return item.get(key, {}).get('value', None)

            # Extract fields
            celebrity = get_val('celebrityLabel')
            spouse = get_val('spouseLabel')
            start_date = get_val('start')
            end_date = get_val('end')
            end_cause = get_val('endCauseLabel')
            c_birth = get_val('c_birth')
            s_birth = get_val('s_birth')
            c_fame = get_val('c_fame')
            s_fame = get_val('s_fame')

            # Clean Dates (Wikidata returns '1990-01-01T00:00:00Z', we want '1990-01-01')
            if start_date: start_date = start_date.split('T')[0]
            if end_date: end_date = end_date.split('T')[0]
            if c_birth: c_birth = c_birth.split('T')[0]
            if s_birth: s_birth = s_birth.split('T')[0]

            results.append({
                "Celebrity": celebrity,
                "Spouse": spouse,
                "Start_Date": start_date,
                "End_Date": end_date,
                "End_Cause": end_cause,
                "Celebrity_Birth": c_birth,
                "Spouse_Birth": s_birth,
                "Celebrity_Fame_Score": c_fame,
                "Spouse_Fame_Score": s_fame
            })

        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Save
        filename = "celebrity_marriages_enriched.csv"
        df.to_csv(filename, index=False)
        
        print("-" * 30)
        print(f"✅ Success! Captured {len(df)} enriched records.")
        print(f"📄 Saved to: {filename}")
        print("-" * 30)
        print(df.head())
        
    else:
        print(f"❌ Wikidata Error: {r.status_code}")

except Exception as e:
    print(f"❌ Script Error: {e}")
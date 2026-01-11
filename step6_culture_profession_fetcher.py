import requests
import pandas as pd
from tqdm import tqdm

# --- CONFIGURATION ---
url = "https://query.wikidata.org/sparql"

# --- THE "CULTURE & PROFESSION" QUERY ---
# Fetching: 
# 1. Country of Citizenship (P27) -> To compare USA vs UK vs India
# 2. Occupation (P106) -> To compare Actors vs Musicians
query = """
SELECT DISTINCT 
  ?celebrityLabel 
  ?spouseLabel 
  ?start ?end ?endCauseLabel
  ?countryLabel
  ?occupationLabel
WHERE {
  # 1. Identify Famous People (General "Human" with > 30 sitelinks)
  ?celebrity wdt:P31 wd:Q5;
             wikibase:sitelinks ?sitelinks.
  FILTER(?sitelinks > 50) 
  
  # 2. Filter for specific professions to compare (Actor, Musician, Athlete)
  VALUES ?occupation { wd:Q33999 wd:Q639669 wd:Q2066131 }
  ?celebrity wdt:P106 ?occupation.
  
  # 3. Marriage Info
  ?celebrity p:P26 ?statement.
  ?statement ps:P26 ?spouse.
  
  OPTIONAL { ?statement pq:P580 ?start. }
  OPTIONAL { ?statement pq:P582 ?end. }
  OPTIONAL { ?statement pq:P1534 ?endCause. }
  
  # 4. Cultural Variable: Country
  OPTIONAL { ?celebrity wdt:P27 ?country. }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
LIMIT 4000
"""

print("🌍 Sending Culture & Profession Query to Wikidata...")

try:
    headers = {'User-Agent': 'CelebrityResearchBot/3.0'}
    r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
    
    if r.status_code == 200:
        data = r.json()
        results = []
        
        print(f"Parsing {len(data['results']['bindings'])} records...")
        
        for item in tqdm(data['results']['bindings']):
            def get_val(key): return item.get(key, {}).get('value', None)
            
            celebrity = get_val('celebrityLabel')
            spouse = get_val('spouseLabel')
            start_date = get_val('start')
            end_date = get_val('end')
            end_cause = get_val('endCauseLabel')
            country = get_val('countryLabel')
            occupation = get_val('occupationLabel')
            
            # Clean Dates
            if start_date: start_date = start_date.split('T')[0]
            if end_date: end_date = end_date.split('T')[0]

            results.append({
                "Celebrity": celebrity,
                "Spouse": spouse,
                "Start_Date": start_date,
                "End_Date": end_date,
                "End_Cause": end_cause,
                "Country": country,
                "Occupation": occupation
            })

        df = pd.DataFrame(results)
        
        # Save
        filename = "celebrity_culture_profession.csv"
        df.to_csv(filename, index=False)
        
        print("-" * 30)
        print(f"✅ Success! Saved '{filename}'")
        print("New Variables:")
        print("1. Country (e.g., USA, India, UK)")
        print("2. Occupation (e.g., Actor, Musician)")
        print("-" * 30)
        print(df.head())
        
    else:
        print(f"❌ Wikidata Error: {r.status_code}")

except Exception as e:
    print(f"❌ Script Error: {e}")
import requests
import pandas as pd
import time

# --- CONFIGURATION ---
# Wikidata SPARQL Endpoint
url = "https://query.wikidata.org/sparql"

# The Query:
# 1. Finds humans (Q5) who are Actors (Q33999).
# 2. Filters for people with > 50 sitelinks (a proxy for "Fame").
# 3. Extracts Spouse, Start Date, End Date, and End Cause.
query = """
SELECT ?celebrity ?celebrityLabel ?spouse ?spouseLabel ?start ?end ?endCauseLabel WHERE {
  ?celebrity wdt:P31 wd:Q5;          # Instance of Human
             wdt:P106 wd:Q33999;     # Occupation: Actor
             wikibase:sitelinks ?sitelinks.
  
  FILTER(?sitelinks > 50)            # ONLY famous people (more than 50 wiki pages exist for them)
  
  ?celebrity p:P26 ?statement.       # "p:P26" means "has a spouse statement"
  ?statement ps:P26 ?spouse.         # Get the spouse
  
  OPTIONAL { ?statement pq:P580 ?start. }      # Get Start Date (if exists)
  OPTIONAL { ?statement pq:P582 ?end. }        # Get End Date (if exists)
  OPTIONAL { ?statement pq:P1534 ?endCause. }  # Get Cause of End (Divorce, Death, etc.)
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
LIMIT 2000
"""

print("🚀 Sending query to Wikidata... (This retrieves 2000 records instantly)")

try:
    # Send the request
    r = requests.get(url, params={'format': 'json', 'query': query})
    data = r.json()
    
    # Parse the JSON result
    results = []
    for item in data['results']['bindings']:
        celebrity_name = item.get('celebrityLabel', {}).get('value')
        spouse_name = item.get('spouseLabel', {}).get('value')
        start_date = item.get('start', {}).get('value')
        end_date = item.get('end', {}).get('value')
        end_cause = item.get('endCauseLabel', {}).get('value')
        
        # Clean up dates (Wikidata returns '2010-01-01T00:00:00Z')
        if start_date: start_date = start_date.split('T')[0]
        if end_date: end_date = end_date.split('T')[0]

        results.append({
            "Celebrity": celebrity_name,
            "Spouse": spouse_name,
            "Start_Date": start_date,
            "End_Date": end_date,
            "End_Cause": end_cause
        })

    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Save to CSV
    filename = "celebrity_marriages_wikidata.csv"
    df.to_csv(filename, index=False)
    
    print("-" * 30)
    print(f"✅ Success! Retrieved {len(df)} marriage records.")
    print(f"📄 Saved to: {filename}")
    print("-" * 30)
    print(df.head())

except Exception as e:
    print(f"❌ Error: {e}")
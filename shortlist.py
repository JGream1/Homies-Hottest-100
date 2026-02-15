from db import SessionLocal, CleanedSong
import requests
import re
import pandas as pd


##### CLEAN SONGS FROM SUBMISSIONS #####

url = 'https://homies-hottest-100.onrender.com/submissions'
data = requests.get(url).json()

# Clean free text values
def clean_text(s):
    if not isinstance(s, str):
        return ''
    
    s = s.upper()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'\s+', ' ', s)

    return s.strip()

# Flatten and remove empty rows
records = []
for sub in data['submissions']:
    homie = sub['name']
    for song, artist, notes in sub['rows']:
        if any(x.strip() for x in [song, artist, notes]):
            records.append({
                'Song': song,
                'Artist': artist,
                'Notes': notes,
                'Homie': homie
            })

df = pd.DataFrame(records)
print(df)

# Normalise to find duplicates
df['Song'] = df['Song'].apply(clean_text)
df['Artist'] = df['Artist'].apply(clean_text)
df['Notes'] = df['Notes'].apply(clean_text)
df = df[df['Song'].str.strip() != '']

final = (
    df.sort_values(['Artist', 'Song', 'Homie'])
      .groupby(['Song', 'Artist'], as_index=False, sort=False)
      .agg({
          'Song': 'first',
          'Artist': 'first',
          'Notes': 'first',
          'Homie': lambda x: ', '.join(sorted(set(x)))
      })
      .sort_values(['Artist', 'Song'])   # <-- final stable sort
      .reset_index(drop=True)
)
print(final)


##### GET COVER ART FOR EACH SONG #####

# Search iTunes for cover art
def search_itunes(song, artist):
    query = f'{song} {artist}'
    url = 'https://itunes.apple.com/search'
    params = {
        'term': query,
        'media': 'music',
        'limit': 1
    }
    
    r = requests.get(url, params=params)

    print("STATUS:", r.status_code)
    print("RAW RESPONSE:", r.text[:300])

    # Raise error if returned
    try:
        r.raise_for_status()
    except Exception as e:
        print("HTTP error:", e)
        return None

    # Try JSON
    try:
        data = r.json()
    except ValueError:
        print("Non-JSON response:")
        print(r.text[:500])
        return None

    results = data.get('results', [])
    if not results:
        return None
    
    artwork = results[0].get('artworkUrl100')
    if not artwork:
        return None
    
    return artwork.replace('100x100bb.jpg', '600x600bb.jpg')

# Add cleaned submission data and image url to cleaned song DB
session = SessionLocal()
session.query(CleanedSong).delete()

for _, row in final.iterrows():
    image_url = search_itunes(row['Song'], row['Artist'])
    cleaned = CleanedSong(
        song=row['Song'],
        artist=row['Artist'],
        notes=row['Notes'],
        image_url=image_url
    )
    session.add(cleaned)

session.commit()
session.close()
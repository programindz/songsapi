from database import songs_collection
import pandas as pd

data = pd.read_csv("data\Spotify_Youtube.csv", encoding = 'latin1', header = 0)

for row in data.itertuples():
    track = {
        'artist': row.Artist.lower().replace(" ",""),
        'link': row.Link,
        'track': row.Track,
        'uri': row.Uri
    }
    songs_collection.insert_one(track)

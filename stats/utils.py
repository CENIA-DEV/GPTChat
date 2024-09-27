import glob
import json
import pandas as pd
# Definir el conteo de países y demás variables como en tu código
country_count = {
    'Argentina': 0, 'Bolivia': 0, 'Brazil': 0, 'Chile': 0, 'Colombia': 0, 
    'Costa Rica': 0, 'Cuba': 0, 'Dominican Republic': 0, 'Ecuador': 0, 
    'El Salvador': 0, 'Guatemala': 0, 'Haiti': 0, 'Honduras': 0, 'Mexico': 0, 
    'Nicaragua': 0, 'Panama': 0, 'Paraguay': 0, 'Peru': 0, 'Uruguay': 0, 
    'Venezuela': 0
}

countries = {
    "Chile": ["gptlas-lcc", "gptlas-cenia", "gptlas-chile"],
    "Argentina": ["gptlas-cordoba"],
    "Mexico": ["gptlas-infotec"],
    "Uruguay": ["gptlas-uru"]
}

types = {"share", "chat", "flag", "bothbad_vote", "downvote", "leftvote", "rightvote", "upvote", "tievote"}

def process_record(r):
    mtype = r.pop("type")
    username = r.pop("username")
    
    if mtype in ("leftvote", "rightvote", "bothbad_vote", "tievote"):
        for country, usernames in countries.items():
            if username in usernames:
                country_count[country] += 1
                break
    return country_count

def process_file(path):
    for key in country_count.keys():
        country_count[key] = 0
    filelist = sorted(glob.glob(path))
    for f in filelist:
        with open(f) as infile:
            for line in infile:
                record = json.loads(line.strip())
                if record.get("tstamp"):
                    process_record(record)
    return country_count.copy()  

def count_country_votes():
    data = process_file("")
    return pd.DataFrame(
        {
            "Países": list(data.keys()),
            "Votos": list(data.values()),
            
        }
    )
import datetime
import glob
import json
from collections import deque
import tqdm
from collections import Counter

def _serialize_json(data):
    # Serialize JSON with sorted keys and no whitespace
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


types = {
    "share",
    "chat",
    "flag",
    "bothbad_vote",
    "downvote",
    "leftvote",
    "rightvote",
    "upvote",
    "tievote",
}
countries = {"Chile":["gptlas-lcc","gptlas-cenia","gptlas-chile"],"Argentina":["gptlas-cordoba"],"Mexico":["gptlas-infotec"],"Uruguay":["gptlas-uru"]}

country_count = {'Argentina':0, 'Bolivia':0, 'Brazil':0, 'Chile':0, 'Colombia':0, 'Costa Rica':0,
    'Cuba':0, 'Dominican Republic':0, 'Ecuador':0, 'El Salvador':0, 'Guatemala':0,
    'Haiti':0, 'Honduras':0, 'Mexico':0, 'Nicaragua':0, 'Panama':0, 'Paraguay':0,
    'Peru':0, 'Uruguay':0, 'Venezuela':0}

cc = []
chat_dict = {}



def process_record(r):
    ip = r.pop("ip", None)
    tstamp = r.pop("tstamp")
    mtype = r.pop("type")
    username = r.pop("username")
    start = r.pop("start", None)
    finish = r.pop("finish", None)


    assert mtype in types
    if mtype == "chat":
        return
    elif mtype in ("leftvote", "rightvote", "bothbad_vote", "tievote"):
        for country, usernames in countries.items():
             if username in usernames:
                country_count[country] += 1
                break
        vote_time_data = {
            "timestamp": tstamp,
            "type": mtype,
            "ip": ip,
            "username":username
        }
        return vote_time_data

    return None


def process_file(infile: str, outfile: str):
    with open(infile) as f:
        records = []
        for l in f.readlines():
            l = l.strip()
            if l:
                try:
                    r = json.loads(l)
                    if r.get("tstamp") is not None:
                        records.append(r)
                except Exception:
                    pass
        # sort the record in case there are out-of-order records
        records.sort(key=lambda x: x["tstamp"])

        with open(outfile, "a") as outfile:
            for r in records:
                try:
                    output = process_record(r)
                    if output is not None:
                        outfile.write(json.dumps(output) + "\n")
                except Exception as e:
                    import traceback

                    print("Error:", e)
                    traceback.print_exc()


def count_votes(path:str):
    today = datetime.datetime.today().isoformat().split("T", 1)[0]
    # sort it to make sure the date is continuous for each server
    filelist = sorted(glob.glob(path))
    # filelist = [
    #     f for f in filelist if today not in f
    # ]  # skip today because date could be partial

    # TODO: change this to select different range of data
    filelist = [f for f in filelist if "2024" in f]

    for f in tqdm.tqdm(filelist):
        process_file(f, "output.jsonl")
    with open("country_count.json","a") as outfile:
        outfile.write(json.dumps(country_count))

    return country_count
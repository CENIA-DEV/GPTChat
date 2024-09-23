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
countries = {"chile":["gptlas-lcc","gptlas-cenia","gptlas-chile"],"argentina":["gptlas-cordoba"],"mexico":["gptlas-infotec"]}

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
                cc.append(country) 
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


today = datetime.datetime.today().isoformat().split("T", 1)[0]
# sort it to make sure the date is continuous for each server
filelist = sorted(glob.glob("/home/sebastiandonoso/GPTChat/logs/202*-*-*-conv.json"))
# filelist = [
#     f for f in filelist if today not in f
# ]  # skip today because date could be partial

# TODO: change this to select different range of data
filelist = [f for f in filelist if "2024" in f]

for f in tqdm.tqdm(filelist):
    process_file(f, "output.jsonl")
country_count = Counter(cc)
print(dict(country_count))
with open("country_count.json","a") as outfile:
    outfile.write(json.dumps(dict(country_count)))

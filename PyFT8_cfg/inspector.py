import json
import numpy as np
import time

def get_calls(file):
    
    with open(file, "r") as f:
        data = json.load(f)

    calls = set()
    for b in data:
        for c in data[b]:
            if b == "2m":
                calls.add(c)
    return calls

#file = "backup/hearing_me1.json"
file = "hearing_me_260421_1652.json"
#file = "hearing_me.json"
#file = "heard_by_me.json"
#file = "heard_by_me_260412_1302.json"

a = get_calls("hearing_me_260421_1652.json")
b = get_calls("hearing_me.json")

diffs = list(a.difference(b))
print(diffs)


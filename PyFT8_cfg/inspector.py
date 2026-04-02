import pickle
import numpy as np
import time


with open("hearing_me.pkl", "rb") as f:
    data = pickle.load(f)

data2 = {}
for b in data:
    band_dict = {}
    for c in data[b]:
        info = data[b][c]
        info.pop('c',None)
        info.pop('new',None)
        info.update({'t':int(info['t']), 'rp':int(info['rp'])})
        band_dict[c] = info
        #print(b,c,info)
    data2[b] = band_dict
        

with open("hearing_me_2.pkl", "wb") as f:
    pickle.dump(data2, f)


with open("hearing_me_2.pkl", "rb") as f:
    data = pickle.load(f)
for c in data2['2m']:
    print(data2['2m'][c])

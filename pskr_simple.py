import threading, time, os, pickle
import xml.etree.ElementTree as ET
import requests

class Pskrdata:
    def __init__(self):
        self.url = "https://retrieve.pskreporter.info/query?receiverCallsign={myCallsign}&statistics=1&noactive=1&nolocator=0"
        self.data = None
        self.datafile = 'pskr_data.pkl'
        self.get_reports()
    
    def get_from_web_pskr(self):
        #requestTime = time.time()
        url = self.url #+ f"&flowStartSeconds={requestTime}"
        print(url)
        response = requests.get(url)
        response.raise_for_status()
        xml_data = response.content
        print("Got data from web")
        return xml_data        

    def save_data(self):
        with open(self.datafile,"wb") as f:
            pickle.dump(self.data, f)

    def get_reports(self):
        if(os.path.exists(self.datafile)):
            with open(self.datafile,"rb") as f:
                try:
                    self.data = pickle.load(f)
                    print("loaded local data")
                    return
                except:
                    pass
        self.data = self.get_from_web_pskr()
        self.save_data()

pskr = Pskrdata()

data = pskr.data
print(type(data))
reports = ET.fromstring(data)
print(ET.tostring(reports, encoding='unicode'))


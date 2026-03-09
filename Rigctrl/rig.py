from .ic7100 import IC_7100
class Rig:
    def __init__(self):
        self.ic7100 = IC_7100()
    def ptt_on(self):
        self.ic7100.setPTTON()
    def ptt_off(self):
        self.ic7100.setPTTOFF()
    def set_freq_Hz(self, freqHz):
        self.ic7100.setFreqHz(freqHz)
    def set_mode(self, md='USB', dat=True, filIdx = 1 ):
        self.ic7100.setMode(md=md, dat=dat, filIdx=filId)
    def get_swr(self):
        return self.ic7100.getSWR()

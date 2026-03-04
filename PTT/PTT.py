from IC_7100.IC_7100 import IC_7100
class PTT:
    def __init__(self):
        self.ic7100 = IC_7100()
    def on(self):
        self.ic7100.setPTTON()
    def off(self):
        self.ic7100.setPTTOFF()

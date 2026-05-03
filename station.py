import numpy as np
import threading
import time
import pickle
import matplotlib.pyplot as plt
import time, queue
from matplotlib import rcParams
from matplotlib.widgets import Slider, Button
from matplotlib.animation import FuncAnimation
import psutil

import serial, socket, subprocess
class Rig:
    def __init__(self,  com = 'COM4', s = 9600, rig = 3070, rigctld = 'C:/WSJT/wsjtx/bin/rigctld-wsjtx'):
        host, port ="localhost", 4532
        if not any(['rigctld' in i.name() for i in psutil.process_iter()]):
            cmd = f"{rigctld} -m {rig} -r {com} -s {s}"
            threading.Thread(target = subprocess.run, args = (cmd,)).start()
            time.sleep(0.5)
        self.sock = socket.create_connection((host, port))

    def cmd(self, command):
        self.sock.sendall((command + "\n").encode())
        try:
            return self.sock.recv(1024).decode()
        except:
            return None

    def _decode_twoBytes(self, twoBytes):
        if(len(twoBytes)==2):
            n1 = int(twoBytes[0])
            n2 = int(twoBytes[1])
            return  n1*100 + (n2//16)*10 + n2 %16

    def set_freq_Hz(self, hz):
        self.cmd(f"F {hz}")

    def ptt_on(self):
        self.cmd(f"T 1")

    def ptt_off(self):
        self.cmd(f"T 0")

    def get_freq_Hz(self):
        return int(self.cmd(f"f"))
    
    def setMode(self, md='PKTUSB', dat=False):
        self.cmd(f"M {md} 0")
        return

    def set_level(self, lvl, lev):
        return self.cmd(f"l {lvl}{lev}")

    def get_level(self, lvl):
        return self.cmd(f"l {lvl}")

    def getSWR(self):
        resp = False
        self.setMode("RTTY")
        #self.set_level('PWR',10)
        self.ptt_on()
        time.sleep(0.01)
        resp_decoded = self.get_level('SWR')
        self.ptt_off()
        self.setMode(md="PKTUSB", dat = True)
        if(resp_decoded):
            return float(resp_decoded)
    
class Arduino:
    def __init__(self, verbose = False, port = 'COM7', baudrate = 9600):
        import serial
        self.good_tunings = {}
        self.serial = serial
        self.serial_port = False
        self.port = port
        self.baudrate = baudrate
        self.verbose = verbose
        self.loop_step = 500
        self.rotator_pos = 180
        self.swr = 3
        self.ready = False
        self.bands = {'160m': (1.8, 2.0), '80m':  (3.5, 3.8), '60m':  (5.25, 5.45),
                 '40m':  (7.0, 7.2), '30m':  (10.1, 10.15), '20m':  (14.0, 14.35),
                 '17m':  (18.068, 18.168),'15m':  (21.0, 21.45),'12m':  (24.89, 24.99),
                 '10m':  (28.0, 29.7), '6m':   (50.0, 52.0), '2m': (144.0, 146.0)}
        self.default_search = {'bands':['80m', '60m', '40m', '30m', '20m', '17m'],
                        'steps': [ np.arange(60,70,1), np.arange(180,190,1), np.arange(265,275,1), np.arange(500,505,1), np.arange(675,685,1), np.arange(845,855,0.5)]}
       # self.load_tunings()
        self.connect()

    def parse_string(self, txt, pos):
        try:
            field = txt[pos:]
            v = int(field)
        except:
            print(f"Couldn't parse {field}")
            return None
        return v

    def get_current_swr(self):
        return self.swr

    def band_from_freq(self, fMHz):
        for band, (lo, hi) in self.bands.items():
            if lo <= fMHz <= hi:
                return band

    def wait_for_ready(self, action_timeout = 120):
        t0 = time.time()
        while not self.ready and (time.time()-t0) < action_timeout:
            time.sleep(0.1)

    def connect(self):
        try:
            self.serial_port = self.serial.Serial(port = self.port, baudrate = self.baudrate, timeout = 0.1)
            if (self.serial_port):
                self.vprint(f"Connected to {self.port}")
        except IOError:
            self.vprint(f"Couldn't connect to {self.port}")

    def stepmap(self, val, maptype):
        if maptype == 'to_degrees':
            return (360-45)*(val-100)/(800-100)
        if maptype == 'to_step':
            return 100+(800-100)*val/(360-45)

    def rotate(self, val):
        stp = self.stepmap(val, 'to_step')
        self.send_command(f"<P{stp}>")

    def monitor(self):
        while True:
            time.sleep(0.02)
            d = self.serial_port.readline().decode('UTF-8')
            if 'CurrStepLoop' in d:
                newval = self.parse_string(d, 13)
                if newval is not None:
                    self.loop_step = newval
            if 'CurrStepRotator' in d:
                newval = self.parse_string(d, 16)
                if newval is not None:
                    self.rotator_pos = self.stepmap(newval, 'to_degrees')
            if 'READY' in d:
                print("[ARD] Ready")
                self.ready = True
            
    def send_command(self, c):
        self.ready = False
        self.vprint(f"[ARD] send {c}")
        self.serial_port.write(c.encode('UTF-8'))

    def load_tunings(self):
        try:
            with open('loop.pkl', 'rb') as f:
                self.good_tunings = pickle.load(f)
            print(self.good_tunings)
        except:
            self.good_tunings = {}
            self.save_tunings()

    def update_tunings(self, fkHz, step):
        if not fkHz in self.good_tunings:
            self.good_tunings[fkHz] = 0
        self.good_tunings[fkHz] = step
        self.save_tunings()

    def save_tunings(self):
        with open('loop.pkl', 'wb') as f:
            pickle.dump(self.good_tunings, f)
        
    def get_tuning(self, fkHz):
        if fkHz in self.good_tunings:
            s = self.good_tunings[fkHz]
            return [s * a for a in np.linspace(0.98, 1.02, 10)]
        else:
            band = self.band_from_freq(fkHz/1000)
            if band in self.default_search['bands']:
                idx = self.default_search['bands'].index(band)
                return self.default_search['steps'][idx]

    def vprint(self, text):
        if self.verbose:
            print(text)

class Gui:
    def __init__(self):
        self.current_kHz = 0
        self.rig = Rig()
        self.station_controller = Arduino(verbose = True)
        threading.Thread(target = self.station_controller.monitor, daemon = True).start()
        self.station_controller.send_command("<QL>")
        self.station_controller.send_command("<QR>")
        self.pmarg = 0.04
        self.make_layout()
        self.tuning_slider.set_val(self.station_controller.loop_step)
        self.pos_slider.set_val(self.station_controller.rotator_pos)
        self.plt.show()

    def _make_buttons(self, buttons, styles, btns_top, btns_left, btn_h, btn_w, step_x, step_y):
        btn_x, btn_y = btns_left, btns_top
        for i, btn in enumerate(buttons):
            btn_axs = plt.axes([btn_x, btn_y, btn_w, btn_h])
            if step_y:
                btn_y -= step_y
            else:
                btn_x += step_x
            style = styles[btn['style']]
            btn_widg = Button(btn_axs, btn['label'], color=style['fc'], hovercolor='skyblue')
            btn_widg.data = btn['data']
            btn_widg.on_clicked(lambda event, btn_widg=btn_widg: self.on_control_click(btn_widg))
            self.buttons.append(btn_widg)
        
    def make_layout(self, wf_left = 0.15, wf_top = 0.87):
        rcParams['toolbar'] = 'None'
        self.plt = plt
        self.fig = plt.figure(figsize = (4,4), facecolor=(.18, .71, .71, 0.4)) 
        self.fig.canvas.manager.set_window_title('Antcontrol by G1OJS')

        self.buttons = []
        styles = {'ctrl':{'fc':'grey','c':'black'}, 'band':{'fc':'green','c':'white'}}
        button_defs = [ {'label':'Tune loop', 'style':'ctrl', 'data':''},
                        {'label':'Check swr', 'style':'ctrl', 'data':''},
                        {'label':'Main = Loop', 'style':'ctrl', 'data':''},
                        {'label':'Main = Dipoles', 'style':'ctrl', 'data':''},
                        {'label':'Rx on main', 'style':'ctrl', 'data':''},
                        {'label':'Rx on alt', 'style':'ctrl', 'data':''}
                        ]
        self._make_buttons(button_defs, styles, btns_top=wf_top, btns_left = 0.1, btn_h = 0.05, btn_w = 0.8, step_x = 0, step_y = 0.06)
        
        # rotator position and indicator
        ax_pos_slider = self.fig.add_axes([0.2, 0.4, 0.6, 0.05])
        self.pos_slider = Slider(ax_pos_slider,  '', 0, 360-45, orientation='horizontal', dragging = False)
        self.pos_slider.vline.set_visible(False)
        self.pos_slider.valtext.set_visible(False)
        self.pos_slider.on_changed(self.rotate)

        self.pos_current = ax_pos_slider.axvline(0, color='blue', lw=2)
        print( ax_pos_slider.get_xticks())
        ax_pos_slider.add_artist(ax_pos_slider.xaxis)
        ax_pos_slider.set_xticks([0,45,90,135,180,225,270,315])
        ax_pos_slider.set_xticklabels(['N','', 'E','', 'S','', 'W',''])

        # swr indicator
        ax_swr_slider = self.fig.add_axes([0.2, 0.2, 0.6, 0.05])
        self.swr_slider = Slider(ax_swr_slider,  'SWR', 1, 3, orientation='horizontal', dragging = False)

        # loop tuning
        ax_tuning_slider = self.fig.add_axes([0.2, 0.1, 0.6, 0.05])
        self.tuning_slider = Slider(ax_tuning_slider,  'Tune step', 30, 900, orientation='horizontal', dragging = True)

    def check_swr(self):
        self.station_controller.swr = self.rig.getSWR()
        self.swr_slider.set_val(self.station_controller.get_current_swr())

    def tune_loop(self):
        self.station_controller.send_command("<ML>")
        fkHz = self.rig.get_freq_Hz()/1000
        print(fkHz)
        steps = self.station_controller.get_tuning(fkHz)
        print(steps)
        if steps is not None:
            self.station_controller.send_command(f"<T{steps[0]}>")
            self.wait_for_controller()
            for step in steps:
                if step > self.station_controller.loop_step:
                    self.station_controller.send_command(f"<T{step}>")
                    self.wait_for_controller()
                    time.sleep(0.2)
                    self.check_swr()
                    if self.station_controller.swr is not None:
                        print(f"Step {self.station_controller.loop_step:6.1f} swr = {self.station_controller.swr:3.1f}")
                        if self.station_controller.swr < 3:
                            self.station_controller.update_tunings(fkHz, step)
                            print("Tuned")
                            return
            print("Done - not tuned")

    def wait_for_controller(self):
        while not self.station_controller.ready:
            self.pos_current.set_xdata([self.station_controller.rotator_pos,self.station_controller.rotator_pos])
            self.tuning_slider.set_val(self.station_controller.loop_step)
            self.fig.canvas.draw()
            self.plt.pause(0.1)

    def rotate(self, val):
        print(val)
        self.station_controller.rotate(val)
        self.wait_for_controller()

    def on_control_click(self, btn_widg):
        txt = btn_widg.label.get_text()
        if txt == 'Check swr':
            self.check_swr()
        if txt == 'Main = Loop':
            self.station_controller.send_command("<ML>")
            t = self.tuning_slider.val
            self.station_controller.send_command(f"<T{t}>")
            self.wait_for_controller()
        if txt == 'Main = Dipoles':
            self.station_controller.send_command("<MD>")
        if txt == 'Rx on main':
            self.station_controller.send_command("<RM>")
        if txt == 'Rx on alt':
            self.station_controller.send_command("<RA>")
        if txt == 'Tune loop':
            if txt == 'Tune loop':
                self.tune_loop()


gui = Gui()


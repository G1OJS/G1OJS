
import numpy as np

detune = 1.1
trapq = 5000
trapr = 0.1

freqs = [50.3, 21.1]
feedlen = 0.1

with open('Trap V.nec','w') as f:
  f.write(f'SY apex = 9\n')
  f.write(f'SY S0 = {feedlen/2:6.3f}\n')
  for i, MHz in enumerate(freqs):
    vlen = 0.95*(1/detune)*143/MHz
    f.write(f'SY S{i+1} = {0.71*vlen/2:6.3f}\n')
    LC = 1/(4.0*np.pi**2*(detune*MHz*1e6)**2)
    L_C = (trapq*trapr)**2
    L = np.sqrt(LC*L_C)
    C = LC/L
    Rd = L/(trapr * C)
    f.write(f'SY ind{i+1} = {L*1e6:6.3f}\n')
    f.write(f'SY cap{i+1} = {C*1e12:6.3f}\n')

  for i, MHz in enumerate(freqs):
    f.write(f"GW\t{10*i+1}\t{5}\t0.000\tS{i}\t-S{i}\t0.000\tS{i+1}\t-S{i+1}\t\t0.005\n")
    f.write(f"GW\t{10*i+2}\t{5}\t0.000\t-S{i}\t-S{i}\t0.000\t-S{i+1}\t-S{i+1}\t\t0.005\n")

  f.write(f"GW\t1000\t1\t0.000\t-S0\t-S0\t0.000\tS0\t-S0\t\t0.005\n")
  f.write(f"GM	0	0	0	0	0	0	0	apex\n")
  f.write('GE\t-1\n')
  f.write('GN 2 0 0 0 11 0.01\n')
  
  for i, MHz in enumerate(freqs[:-1]):  
    f.write(f"LD\t1\t{10*i+1}\t{5}\t{5}\tind{i+1}/({trapr} * cap{i+1}*1e-6)\tind{i+1}*1e-6\tcap{i+1}*1e-12\n")
    f.write(f"LD\t1\t{10*i+2}\t{5}\t{5}\tind{i+1}/({trapr} * cap{i+1}*1e-6)\tind{i+1}*1e-6\tcap{i+1}*1e-12\n")
  
  f.write(f"EX\t0\t1000\t1\t0\t1\t0\n")
  f.write(f"FR\t0\t0\t0\t0\t{freqs[0]}\t0\n")
  f.write("EN\n")

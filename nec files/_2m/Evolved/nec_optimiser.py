import subprocess, os, time
import numpy as np
NEC_EXE = "C:\\4nec2\\exe\\nec2dxs11k.exe"

def run_nec(model_name, silent = True):
    for filepath, content in [('nec.bat', f"{NEC_EXE} < {'files.txt'} \n"),('files.txt', f"{model_name}.inp\n{model_name}.out\n")]:
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        try:
            with open(filepath, "w") as f:
                f.write(content)
        except Exception as e:
            print(f"Error writing file {filepath}: {e}")
    try:
        os.remove(f"{model_name}.out")
    except FileNotFoundError:
        pass
    if not silent: print("Running NEC")
    subprocess.Popen(['nec.bat'], creationflags=subprocess.CREATE_NO_WINDOW)
    factored = False
    pattern_started = False
    st = time.time()
    while True:
        try:
            with open(f"{model_name}.out", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if "FACTOR=" in line and not factored:
                        factored = True
                        if not silent: print("Matrix factored")
                    if "RADIATION" in line and not pattern_started:
                        pattern_started = True
                        if not silent: print("Calculating pattern")
                    if "ERROR" in line:
                        raise Exception(f"NEC Error: {line.strip()}")
                    if "RUN" in line:
                        if not silent: print("NEC run completed")
                        return  # success
        except FileNotFoundError:
            pass  # Output not yet created
            if time.time() - st > 10:
                raise Exception("Timeout waiting for NEC to start")
        time.sleep(0.5)

def write_inp(model_name, params, freqs):
    def point_str(xyz):
        return ' '.join([f"{c:6.3f}".strip() for c in xyz])
    
    apex = 0
    feedlen = 0.1

    with open(f"{model_name}.inp",'w') as f:
      f.write("CE\n")
      s = params[0]
      start_right, start_left = s, [-s[0],s[1],s[2]]
      f.write(f"GW {500} {1} {point_str(start_left)} {point_str(start_right)} 0.005\n")
      for i, s in enumerate(params[1:]):
        end_right, end_left = s, [-s[0],-s[1],s[2]]
        f.write(f"GW {10*i+1} {1} {point_str(start_right)} {point_str(end_right)} 0.005\n")
        f.write(f"GW {10*i+2} {1} {point_str(start_left)} {point_str(end_left)} 0.005\n")
        start_right, start_left = end_right, end_left
      f.write(f"GM 0 0 0 0 0 0 0 {apex}\n")
      f.write('GE 0\n')
      #f.write('GE -1\n')
      #f.write('GN 2 0 0 0 11 0.01\n')
      f.write('EK\n')      
      f.write(f"EX 0 500 1 0 1 0\n")
      for MHz in freqs:
          f.write(f"FR 0 0 0 0 {MHz} 0\n")
          f.write("XQ\n")

def get_swrs(model_name, freqs):
    with open(f"{model_name}.out",'r') as f:
        lines = f.readlines()
    i = 0
    swrs = []
    for MHz in freqs:
        while True:
            i +=1
            l = lines[i]
            if "ANTENNA INPUT PARAMETERS" in l:
                l = lines[i+4]
                break
        z = float(l[60:72]) + 1j * float(l[72:84])
        if z.real > 1:
            mg = np.abs((z-50)/(z+50))
            swrs.append( float((1+mg)/(1-mg)) )
        else:
            swrs.append(1e9)
    return swrs
        

model = 'Test'
freqs = [144.2]
nsegs = 30
l0 = 0.2*143/144.2
best = [[0.02, 0, 0]] + [[x,0,0] for x in 0.5*l0*(1+np.arange(nsegs))/nsegs ]
test = best
write_inp(model, best, freqs)
run_nec(model)
s = get_swrs(model, freqs)
cost = np.sum(s)
print(s)

a = 0.0001
for it in range(1000):
    for i in range(1, nsegs):
        for j in range(3):
            test[i][j] = best[i][j] + a * np.random.random(1)[0]
    x_fact = np.max([t[2] for t in test]) / (l0/2)
    if x_fact > 1:
        for i, t in enumerate(test):
            test[i][0] /= x_fact 
        

                
    write_inp(model, test, freqs)
    run_nec(model)
    s = get_swrs(model, freqs)
    test_cost = np.sum(s)
    if test_cost < cost:
        best = test
        cost = test_cost
        print("Improved:")
        print(','.join([f"{sx:6.3f}" for sx in s]))
    


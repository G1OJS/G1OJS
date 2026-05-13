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
    
    apex = 9
    feedlen = 0.1
    vlen = params['vlen']

    with open(f"{model_name}.inp",'w') as f:
      f.write("CE\n")
      start_right, start_left = [0, feedlen, -feedlen], [0, -feedlen, -feedlen]
      f.write(f"GW {500} {1} {point_str(start_left)} {point_str(start_right)} 0.005\n")
      for i, s in enumerate(params['posns']+[1]):
        end_right, end_left = [0, 0.71*s*vlen/2, -0.71*s*vlen/2], [0, -0.71*s*vlen/2, -0.71*s*vlen/2]
        f.write(f"GW {10*i+1} {5} {point_str(start_right)} {point_str(end_right)} 0.005\n")
        f.write(f"GW {10*i+2} {5} {point_str(start_left)} {point_str(end_left)} 0.005\n")
        start_right, start_left = end_right, end_left
      f.write(f"GM 0 0 0 0 0 0 0 {apex}\n")
      f.write('GE -1\n')
      f.write('GN 2 0 0 0 11 0.01\n')
      
      for i, ind in enumerate(params['inds']):
        f.write(f"LD 1 {10*i+1} {5} {5} {1e7} {ind*1e-6:8.3e} {3e-12:8.3e}\n")
        f.write(f"LD 1 {10*i+2} {5} {5} {1e7} {ind*1e-6:8.3e} {3e-12:8.3e}\n")
      
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
        mg = np.abs((z-50)/(z+50))
        swrs.append( float((1+mg)/(1-mg)) )
    return swrs
        

model = 'Test'
freqs = [7.07, 14.1]
best = {'vlen':13.8, 'inds':[33.1], 'posns':[0.943]}
write_inp(model, best, freqs)
run_nec(model)
s = get_swrs(model, freqs)
cost = np.sum(s)
print(s)


a = 0.001
for it in range(100):
    r = 1+a*np.random.random(5)-a/2
    test = {'vlen':best['vlen'], 'inds':[best['inds'][0]*float(r[1])],
            'posns':[best['posns'][0]*float(r[3])]}
    write_inp(model, test, freqs)
    run_nec(model)
    s = get_swrs(model, freqs)
    test_cost = np.sum(s)
    if test_cost < cost:
        best = test
        cost = test_cost
        print("Improved:")
        print(','.join([f"{k}:{v}" for k,v in best.items()]))
        print(','.join([f"{sx:6.3f}" for sx in s]))
    


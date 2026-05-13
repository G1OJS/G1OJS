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


def get_points(angles, dzs, l0):
    lseg = 0.5*l0/(len(angles))
    xyz = [[lseg/2, 0, 0]]
    aa = 0
    for i, a in enumerate(angles):
        aa += a
        xyz_next = [xyz[-1][0] + lseg * np.cos(aa), xyz[-1][1]+ lseg * np.sin(aa), xyz[-1][2] + dzs[i]]
        xyz.append( xyz_next )
    xfact = 0.5*l0/np.max([p[0] for p in xyz])
    for p in xyz:
        p[0] *= xfact
        p[1] *= xfact
       # p[2] *= xfact
    return xyz

model = 'Test5'
freqs = [144.2]
l0 = 0.25*143/144.2
best_a = np.zeros(15)+10*np.pi/180
best_dz = np.zeros(15)
cost = 1e9

a0 = np.pi*2/180
for it in range(50):
    a0 *=0.995
    test_a = best_a
    test_dz = best_dz
    if it>0:
        i = int(1+(len(test_a)-1)*np.random.random(1)[0])
        test_a[i] += a0*(np.random.random(1)[0])
        #test_dz += 0.001*(np.random.random(len(test_a))-0)
    xyz = get_points(test_a, test_dz, l0)
    write_inp(model, xyz, freqs)
    run_nec(model)
    s = get_swrs(model, freqs)
    test_cost = np.sum(s)
    if test_cost < cost:
        best_a = test_a
        best_dz = test_dz
        cost = test_cost
        print(f"{it}: (a0={a0*180/np.pi:6.1f}) improved:")
        print(','.join([f"{sx:6.3f}" for sx in s]), ','.join([f"{sx*180/np.pi:6.1f}" for sx in best_a]), ','.join([f"{sx:6.3f}" for sx in best_dz]))
    if(test_cost < 1.5):
        break

xyz = get_points(best_a, best_dz, l0)
for p in xyz:
    print(','.join([f"{s:6.3f}" for s in p]))
write_inp(model, xyz, freqs)

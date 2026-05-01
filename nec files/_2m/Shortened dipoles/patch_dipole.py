

with open('Patch dipole.nec', 'w') as f:
    f.write("sy wd = 0.005\n")
    f.write("sy ld = 0.67\n")
    f.write("sy hd = 0.36\n")
    f.write("sy g = 0.044\n")
    f.write("sy lp = (ld-g)/2\n")
    f.write("sy dz = 0.15\n")
    nx, ny = 10, 10
    itag = 0
    for i in range(0, nx):
        x_plus = f"g/2+{i}*lp/{nx-1}".replace("+-","-")
        x_minus = f"-g/2-{i}*lp/{nx-1}".replace("--","+")
        y0 = "-hd/2"
        y1 = "hd/2"
        f.write(f"GW\t{itag:<6}\t{2*(ny-1):<6}\t{x_plus}\t{y0}\t0.000\t{x_plus}\t{y1}\t0.000\twd/2\n")
        itag +=1
        f.write(f"GW\t{itag:<6}\t{2*(ny-1):<6}\t{x_minus}\t{y0}\t0.000\t{x_minus}\t{y1}\t0.000\twd/2\n")
        itag +=1
    for i in range(-ny +1, ny):
        y = f"{i}*0.5*hd/{ny-1}".replace("+-","-")
        x0 = "g/2"
        x1 = "(g/2+lp)"
        f.write(f"GW\t{itag:<6}\t{nx-1:<6}\t{x0}\t{y}\t0.000\t{x1}\t{y}\t0.000\twd/2\n")
        itag +=1
        f.write(f"GW\t{itag:<6}\t{nx-1:<6}\t-{x0}\t{y}\t0.000\t-{x1}\t{y}\t0.000\twd/2\n")
        itag +=1
        
    f.write(f"GW\t{itag:<6}\t1\t-g/2\t0.000\t0.000\tg/2\t0.000\t0.000\twd/2\n")
    f.write("GM	100	1	0	0	0	0	0	dz\n")
    f.write("GE 0\n")
    f.write("EK\n")
    f.write(f"EX 0 {itag} 1 0 1 0\n")
    f.write("FR	0	1	0	0	144.2	0\n")
    f.write("RP 0 37 37 1003 0 0 5 10.0\n")
    f.write("EN\n")

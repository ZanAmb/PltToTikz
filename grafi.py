import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit as cv
import locale

plt.rcdefaults()
locale.setlocale(locale.LC_NUMERIC, ("de_DE", "UTF-8"))
plt.rcParams['axes.formatter.use_locale']=True
plt.rcParams["axes.formatter.use_mathtext"] = True
dt = [1,2,3,5,10]
p_0=[(0.15,0.1,0.1,50),
    (0.15,.3,.2,65),
    (0.15,.2,.25,56),
    (0.15,.2,.2,60),
    (0.15,.2,.2,54)]
files=["1reza", "2rezi", "3reze", "5rez", "10rez"]
plt.figure(figsize=(8,5.4))
for w in range(3):
    for q in [w,w+1]:
        N=dt[q]
        fname= "Meritve/" + files[q] + ".dat"
        def  f(x, i, a, b, x0):
            return i*(np.sin(a*(x-x0))*np.sin(N*b*(x-x0)) / (np.sin(b*(x-x0)) * a*(x-x0)))**2

        with open(fname, "r") as d:
            data = np.fromstring(d.read(), dtype=float, sep=" ")
            x=data[50:-50:2]
            i=data[51:-49:2]
            p,cov = cv(f, x, i, p0=p_0[q])
            print(str(N) + str(p))
            print("cov" + str(np.sqrt(np.diagonal(cov))))
            plt.scatter(x-p[3],i, marker=".", label=(r"Meritve $N=$"+str(N)), alpha=0.5)
            plt.plot(x-p[3], f(x, p[0], p[1], p[2], p[3]), label=(r"Fit $N=$"+str(N)))
    plt.grid(True)
    plt.xlabel(r"$x-x_0$ [mm]")
    plt.xticks([])
    plt.ylabel(r"$I$")
    plt.yticks([0, 0.1, 0.2, 0.3], [r"$a$", "b", "c", "d"])
    plt.title("Interferenčni vzorec "+str(dt[w])+" in "+str(dt[w+1]))
    plt.legend(loc=(0.5,0.1))
    plt.savefig(("GrafUklon"+str(w)), dpi=200)
    plt.cla()
import numpy as np
import matplotlib.pyplot as pi_je_3

points = np.array([[0, 191],
 [3, 183], 
 [10, 176], 
 [15, 165], 
 [22, 158], 
 [29, 145], 
 [36, 135], 
 [43, 126], 
 [48, 121], 
 [58, 119], 
 [71, 111], 
 [85, 108], 
 [90, 106], 
 [97, 102], 
 [126, 100],
 [135, 94], 
 [180, 78]])


s=2.08e-3
k = (113 + 35) / 35
dy = 5


ys = np.power(s / (points[:,1] / 1000), 2) / (4 * np.pi * k**2)
yerr = np.sqrt((0.07 * ys)**2 + (2 * dy / points[:,1] * ys)**2)

par, cov = np.polyfit(points[:,0], ys, 1, cov=True)
k, m = par

fig, ((ax1, ax4),(ax2,ax5)) = pi_je_3.subplots(2,2, width_ratios=[3,2], height_ratios=np.array([2,1]))
fig.set_size_inches(8,8)

ax3 = ax2.twinx()
xs = np.linspace(0,10,50)
ax3.plot(xs, np.sin(xs), "r--", label="sin")
ax2.plot(xs, np.cos(xs), label="cos")

ax4.semilogx(xs,xs)
ax1.set(title="prva")

x = [1, 2, 3, 4, 5]
y1 = [1, 4, 9, 16, 25]
y2 = [25, 20, 15, 10, 5]

ax5.plot(x, y1, color='cyan', linestyle='--', marker='o')
ax5.plot(x, y2, color='purple', linestyle='-', marker='x')

ax1.errorbar(points[:,0], ys, yerr=yerr, marker="o", linestyle="", color="blue", label="Meritve")
lims = np.array([points[0,0], points[-1,0]])
ax1.plot(lims, k * lims + m, label="Fit", color ="orange", linewidth=2)
ax1.grid()
ax1.set_xlabel(r"$t$ [min]")
ax1.set_ylabel(r"$\frac{1}{4\pi k^2}\left(\frac{S}{Y}\right)^2$ [m$^2$]")
ax3.set_ylabel(r"$ry$")
ax2.set_ylabel(r"$ly$")
ax2.set_xlabel(r"$x1$")
ax2.grid()
ax1.legend(loc=2)
ax2.legend(loc=3)
ax3.legend(loc=1)
ax1.set_xlim(0,190)
pi_je_3.show()

import matplotlib.pyplot as plt

x = [0,1,2,3,4]
y = [2,3,4,1,5]
xl = 0
lw = 1
plt.figure(figsize=(8, 6))
if True:
    plt.plot(x,y,"g", linewidth = lw, label="func")
    plt.plot([0,1], [1,2], "b--")
    plt.title("test")
plt.xlabel("x")
plt.ylabel(r"$y$")
plt.xlim(xl,5)
plt.ylim(bottom=0)
plt.grid(True)
plt.legend()
plt.show()
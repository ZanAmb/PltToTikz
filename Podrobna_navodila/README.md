Potrebni paketi:
- matplotlib,
- ast (`pip install astor`).

Program morate pognati iz direktorija, v katerem bi delovala tudi vaša koda za graf (če berete zunanje datoteke prek relativnih poti)!

Sliko v svojo .tex datoteko dodate kot `\input{xxx.tikz}`, za delovanje sta potrebna paketa `tikz` in `pgfplots`.

Podprte nastavitve:
- tip grafa: plot, scatter, stackplot, errorbar,
- subplots (več grafov v eni sliki),
- dvojne y-osi,
- logaritemska skala osi,
- decimalna vejica in pika (lahko tudi za tisočice; če je nastavljena v Matplotlibu prek locale),
- meje osi (oboje, spodnja, zgornja),
- oznake osi in pripadajoče črte,
- naslov,
- mreža (osnovno),
- velikost (osnovno),
- legenda (samodejno ugotavljanje najboljše lokacije še ni implementirano),
- prosojnost grafov,
- izbira markerja (ni še vseh opcij) in velikost,
- debelina črte,
- barva grafa,

Nekatere (še) nepodprte nastavitve:
- 3D grafi,
- prikaz matrik, spektrogramov,
- barvne sheme,
- ...


Opažene napake in predloge lahko javite v GitHubov Issues tega projekta. Trenutna najnovejša verzija je v0.6.

Uvoziti `matplotlib.pyplot as xxx`, kjer je `xxx` lahko katerokoli za Python veljavno ime. Predpogoj za pretvorbo je, da Pythonov program steče do konca (morebitne `plt.show()` okna morate zapreti), šele nato se začne pretvroba.

Podroben nabor podprtih ukazov:
| Matplotlib Command | Opis, opombe |
|:-------------------|:--------------------------|
| `plot(x, y, **kwargs)` | Standarden graf, možnosti navedene spodaj |
| `scatter(x, y, **kwargs)` | Nepovezane točke |
| `errorbar(x, y, **kwargs)` |  Graf z napakami, možnost navedene spodaj|
| `semilogx(x, y, **kwargs)` | Logaritemska x skala |
| `semilogy(x, y, **kwargs)` | Logaritemska y skala |
| `loglog(x, y, **kwargs)` | Logaritemski obe skali |
| `stem(x, y, **kwargs)` | Točke, povezane z x-osjo|
| `axvline(x=0, ymin=0, ymax=1, **kwargs)` | Navpična črta, limite podane relativno glede na os [0,1]*|
| `axhline(y=0, xmin=0, xmax=1, **kwargs)` | Vodoravna črta, limite podane relativno glede na os [0,1]*|
| `vlines(x, ymin, ymax, **kwargs)` | Navpične črte|
| `hlines(y, xmin, xmax, **kwargs)` | Vodoravne črte|

---
*Skupna legenda dvojnih osi za to ni podprta, rišite na tisti osi, na kateri nato kličete `legend()`.

| Matplotlib Keyword | Opis, opombe |
|:-------------------|:--------------------------|
| `label="..."`| Ime za legendo|
| `color="..."`  | Z besedo, RGB, HEX, skrajšano |
| `marker="..."` | Tip točk|
| `markersize=n`  |Velikost točk |
| `linestyle="--"` / `":"` / `"-."` -> `dashed`, `dotted`, `dashdot` | Slog črte |
| `linewidth=n` | Debelina črte |
| `alpha=n` | Prosojnost |
| `xerr`, `yerr`  | Napake se podaja kot konstanto, polje/seznam ali polje za ločene zg./sp. oz. leve/desne |
| `fmt` (e.g. `'r--'`)  | Skrajšana oblika stila in barve|

---

| Matplotlib Command  | Opis, opombe |
|:-------------------|:--------------------------|
| `plt.subplots(nrows, ncols, ...)` |  S tem sliko razbijemo na `fig` in več osi, ki naj bodo EKSPLICITNO izražene na levi strani enačaja (shranjevanje osi kot `Iterable` še ni podprto), razmerje širin višin nastavimo s `width_ratios` oz. `height_ratios`. Možnosti deljenih osi še ni (če vsebina nima enakega razpona in morajo biti osi enake, je treba ročno nastaviti limite za vsako posebej. |
| `ax.twinx()` | | Dobimo sekidnarno y-os |
| `plt.show()` / `plt.savefig()` | Prikaz/shranjevanje slike avtomatično shrani tudi `.tikz` graf |

---
Pri shranjevanju se ohrani ime, končnica pa se zamenja. V primeru uporabe `plt.show()` lahko ime izhodne `.tikz` datoteke nadzirate tako, da v vrstici, ki je neposredno nad ukazom, dodate `#name: xxx`. Če imena ne določite, se poimenuje kot ime programa z zaporedno številko grafa.   
| Matplotlib Command | Opis, opombe |
|:-------------------|:--------------------------|
| `ax.set_xlabel(label)` | Oznaka osi x|
| `ax.set_ylabel(label)` |  | Oznaka osi y |
| `ax.set_title(label)` / `ax.set(title="...")`  | Naslov grafa |
| `ax.set_xlim(left, right)` | Meje osi x |
| `ax.set_ylim(bottom, top)`  | Meje osi y |
| `ax.grid(True)` | `grid=both` | Zaenkrat le vklopi mrežo |
| `ax.set_xscale("log", base=10)` | Logaritemska x skala |
| `ax.set_yscale("log", base=10)` | Logaritemska y skala |
| `plt.figure(figsize=(w,h))` / `ax.figure(figsize=(w,h))` | Nastavi velikost izhodne slike (pretvorba ni direktna, poskuša imitirati skaliranje, 1 enota je pribl. 2cm |
| `fig.set_size_inches(w, h)` | Enako, le za figuro, kar bo delalo v primeru uporabe `subplot()` |
| `ax.legend(loc=...)` | Lokacija legende (avtomatski način ni implementiran |
| `ax.set_xticks([...])`, `ax.set_xticklabels([...])` | Točke na osi x in njihova imena|
| `ax.set_yticks([...])`, `ax.set_yticklabels([...])` |Točke na osi y in njihova imena |

---
LEGENDA: Pri dvojnih oseh je težko narediti enotno legendo v Pythonu, zato v primeru, da vsaj na eni od osi kličete `legend()`, LaTeX verzija grafa prikaže vse poimenovane grafe (vse s parametrom `label`). Pozor: grafi sekundarne osi lahko prečkajo legendo primarne. Ročno koordiante nastavimo kot `loc=(x,y)`, kjer podamo relativne koordinate levega spodnjega kota na intervalu [0,1].

Demonstracijski primer (brez ročnih popravkov, v0.5, koda spodaj):
<img width="775" height="750" alt="image" src="https://github.com/user-attachments/assets/bbe8e4ab-93c8-4398-afae-1d78fe9ca02b" />
<img width="775" height="750" alt="image" src="https://github.com/user-attachments/assets/45783e92-6482-4e1d-9d83-ba926c8ab825" />



Demonstarcijski primer (privzete barve, v0.3):


<img width="1000" height="675" alt="GrafUklon0" src="https://github.com/user-attachments/assets/0685f035-f40b-46b0-9ca0-fa4c54275148" />

<img width="1000" height="606" alt="image" src="https://github.com/user-attachments/assets/2b7b8c96-1ca5-4ddf-a2d5-92b3c9d7d1cf" />















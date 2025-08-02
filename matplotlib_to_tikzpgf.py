# v0.2 development

import re
import ast      # pip install astor
import os

count = 0
def export_graph(final, _graph_arguments, _plots):
    global count
    global dci
    dci = []
    tikz_code = r"""\begin{tikzpicture}
    \begin{axis}["""+ "\n" + \
    _graph_arguments + "\n" + \
    """]\n""" + \
    _plots + "\n" + \
    r"""
    \end{axis}
    \end{tikzpicture}
    """
    name = ""
    if not (final and count == 0):
        name = count
        count += 1
    with open(path.replace(".py", f"{name}.tex"), "w") as f:
        f.write(tikz_code)

ConvertStyle = False # experimental

print("Python file with plot to convert: ")
inp = input()
path = re.sub(r"\\", r"/", inp)
#print("Try converting settings (experimental, should work on simple setups without logic and loops, one plt.show()/plt.savefig())? [y/N]:")
#if "y" in input().lower():
#    ConvertStyle = True

file = []
with open(path, "r") as f:
    file = f.readlines()

file.insert(0, "_datas = []\n_cmds = {}\n_cmds_list = []")
i = 1
while i < len(file):
    if any(f"plt.{plttype}" in file[i] for plttype in ["plot", "scatter", "stackplot"]):
        tree = ast.parse(file[i].strip())
        call = tree.body[0].value
        args = [ast.unparse(arg) for arg in call.args]
        kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in call.keywords]
        spaces = list(re.search(r"^([\s\#]*)plt\.([\w]+)\(", file[i]).groups())
        ptype = spaces[-1]
        if len(spaces) == 2:
            spaces = spaces[0]
        else:
            spaces = ""
        x, y = args.pop(0), args.pop(0)
        controls = ""
        for arg in args:
            controls += f"str({arg}), "
        for kwarg in kwargs:
            spl = kwarg.split("=")
            k, v = spl[0], "=".join(spl[1:])
            controls += f"(\"{k}\", str({v})), "
        controls = controls.removesuffix(", ")
        file.insert(i, spaces + f"_datas.append([\"{ptype}\", {x}, {y}, {controls}])")
        i += 1
    elif "plt.show()" in file[i] or "plt.savefig(" in file[i]:
        spaces = re.search(r"^([\s\#]*)plt\.", file[i]).groups()
        if spaces:
            spaces = spaces[0]
        else:
            spaces = ""
        file.insert(i, spaces + f"_cmds_list.append(_cmds.copy())")
        file.insert(i, spaces + f"_datas.append([\"end\"])")
        i += 2
    elif "plt." in file[i]:
        groups = re.search(r"^([\s\#]*)plt\.([\w]+)\((.*)\)$", file[i])
        if groups:
            spaces, cmd, fargs = groups.group(1), groups.group(2), groups.group(3)
            tree = ast.parse(f"f({fargs})")
            call=tree.body[0].value
            args = [ast.unparse(arg) for arg in call.args]
            kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in call.keywords]
            controls = ""
            for arg in args:
                controls += f"str({arg}), "
            for kwarg in kwargs:
                spl = kwarg.split("=")
                k, v = spl[0], "=".join(spl[1:])
                controls += f"(\"{k}\", str({v})), "
            controls = controls.removesuffix(", ")
            file.insert(i, spaces + f"_cmds[\"{cmd}\"] = [{controls}]")
            i += 1
    i += 1

default_graph_arguments = {"width": "13cm", "height": "10cm"}
file = "\n".join(file)
namespace = {}
exec(file, namespace)
datas = namespace["_datas"]
#cmds = namespace["_cmds"]
cmds_list = namespace["_cmds_list"]
rcP = namespace["plt"].rcParams
try:
    locale = namespace["locale"].localeconv()
    decimal_sep = locale["decimal_point"]
    th_sep = locale["thousands_sep"]

    default_graph_arguments["xticklabel"] = default_graph_arguments["yticklabel"] = r"{\pgfmathprintnumber[assume math mode=true,1000 sep={" + th_sep + r"},dec sep={" + decimal_sep + r"}]{\tick}}"
except: None

anchor_map = {"top": "north", "bottom": "south", "left": "west", "right": "east", "center": "center"}

legend = False
def find_def(k, vals):
    output = {}
    if "lim" in k:
        if len(vals) == 2:
            sp, zg = str(k).replace("lim", "min"), str(k).replace("lim", "max")
            output[sp]=vals[0]
            output[zg]=vals[1]
        else:
            v = vals[0]
            s = str(v[0]).strip().replace("left", "min").replace("bottom", "min").replace("right", "max").replace("top", "max")
            output[k[0]+s]=v[1]
    elif "legend" in k:
        global legend
        legend = True
        #print("Legend position? (use decimal dot (.))")
        #print("x/width: ")
        #x = input()
        #print("y/height: ")
        #y = input()
        #print("Anchor(e.g north east): ")
        #anc = input()
        #k = "legend style"
        #v = r"{at={(" + f"{x},{y}" + r")}, anchor=" + anc + r"}"
        #output[k] = v
    else:
        for v in vals:
            if "title" in k:
                if isinstance(v, tuple):
                    if "loc" in v[0]:
                        output["title style"] = r"{align=" + v[1] + r"}"
                else:
                    output["title"] = r"{" + v + r"}"
            elif k.strip() in ["ylabel", "xlabel"]:
                if isinstance(v, tuple):
                    if "loc" in v[0]:
                        output[f"{k} style"] = r"{anchor=" + anchor_map[v[1]] + r"}"
                else:
                    output[k] = r"{" + v + r"}"
            elif k == "grid":
                if v.strip() == "True":
                    v = "both"
                output[k] = v
            elif k.strip() == "figure":
                if v[0].strip() == "figsize":
                    dims = re.search(r"\(\s*(\S+)\s*\,\s*(\S+)\s*\)", v[1])
                    w, h = float(dims.group(1)), float(dims.group(2))
                    w -= 0.9
                    h -= 1.1
                    w *= 2
                    h *= 2
                output["width"] = f"{w:.2f}cm"
                output["height"] = f"{h:.2f}cm"

    return output

gas_list = []
gas = default_graph_arguments
for cmds in cmds_list:
    for cmd in cmds:
        gas.update(find_def(cmd, cmds[cmd]))

    graph_arguments = ""
    for ga in gas:
        graph_arguments += f"\t{ga}={gas[ga]},\n"
    graph_arguments = graph_arguments.removesuffix(",\n")
    gas_list.append(graph_arguments)

color_map = {'b':'blue', 'g':'green', 'r':'red', 'c':'cyan', 'm':'magenta', 'y':'yellow', 'k':'black', 'w':'white'}
marker_map = {'o':'*', ".": "*", 's':'square*', '^':'triangle', 'v':'triangle*', 'd':'diamond', '+':'+', 'x':'x', '*':'star'}
line_map = {"--": "dashed", ":": "dotted", "-.": "dashdot"}
default_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
dci = []

def hex_to_pgf(hex):
    c = []
    for i in [1,3,5]:
        c.append(int(hex[i:i+2], 16) / 255)
    return r"{rgb:" + f"red,{c[0]:.2f};green,{c[1]:.2f};blue,{c[2]:.2f}" + r"}"

plots = ""
while datas:
    col = None
    p = datas.pop(0)
    if len(p) == 1:
        export_graph(False, gas_list[count], plots)
        plots = ""
        continue
    label = ""
    ptype = p.pop(0)
    style = []
    for arg in p[2:]:
        if isinstance(arg, tuple):
            st = arg[0]
            if "label" in st:
                label = arg[1]
            else:
                k, v = arg[0], arg[1]
                if "alpha" in k:
                    style.append(f"opacity={v}")
                elif "marker" == str(k).strip():
                    marker = next((marker_map[m] for m in arg if m in marker_map), "*")
                    style.append(f"mark={marker}")
                elif "linewidth" in k:
                    style.append(f"line width={v}pt")
                elif "markersize" in k:
                    style.append(f"mark size={v/2:.2f}pt")
                elif "color" in k:
                    col = hex_to_pgf(v)
        else:
            color = next((color_map[c] for c in arg if c in color_map), None)
            marker = next((marker_map[m] for m in arg if m in marker_map), None)
            line = next((line_map[m] for m in line_map if m in arg), None)
            if color:
                col = color
            if marker:
                style.append(f"mark={marker}")
            if line:
                style.append(f"{line}")
    if col == None:
        col = hex_to_pgf(default_colors[dci.count(ptype)])
        dci.append(ptype)
    style.append(f"color={col}")
    if ptype == "scatter":
        style.append("only marks")
    if ptype == "stackplot":
        style.append(f"fill={col}")
    style = ", ".join(style)
    plots += f"\n\\addplot [{style}] coordinates {{\n"
    x,y = p[0], p[1]
    for i in range(len(x)):
        plots += f"\t({x[i]}, {y[i]})\n"
    plots += "};\n"
    if len(label) > 0 and legend:
        plots += f"\\addlegendentry{{{label}}}"
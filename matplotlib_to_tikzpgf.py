# v0.5 development

import re
import ast      # pip install astor
import os

# ================ SETTINGS ================
OVERRIDE_DECIMAL_SEP = ","  # leave empty for auto
OVERRIDE_1000_SEP = ""      # use x for auto
DIRECT_FIGSIZE = False      # use number of inch in matplotlib as number of cm in LaTeX


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
    with open(path.replace(".py", f"{name}.tikz"), "w") as f:
        f.write(tikz_code)

dev_mode = False

file = []
if dev_mode:
    path = "./test_plot.py"
    with open(path, "r") as f:
        file = f.readlines()
else:
    print("Python file with plot(s) to convert (on WinOS you may drag it in here): ")
    while len(file) == 0:
        inp = input()
        path = re.sub(r"\\", r"/", inp)
    
        if path.split(".")[-1] != "py":
            print("Not a .py file. Try again:")
            continue
        try:
            with open(path, "r") as f:
                file = f.readlines()
        except:
            print("Error reading your file. Try again:")

file.insert(0, "_axis = {\"default\": {\"datas\": [], \"cmds\": {}, \"plt_no\": 0}}\n_axis_list=[]\n")
i = 0
plt_name = ""
axis = {}
a_num = 0
while not plt_name and i < len(file):
    if "import matplotlib.pyplot" in file[i]:
        q = file[i].split(" as ")
        plt_name = q[1].strip()
        axis = {0: {"axis" : [plt_name], "fig": None}}
    i += 1
while i < len(file):
    if f"{plt_name}.subplots" in file[i]:
        sbplt_data = list(re.search(r"^([\s\#]*)([a-zA-Z0-9_]*),(.*)=\s*" + plt_name + r"\.subplots\((.+)\)\s*$", file[i]).groups())
        spaces = sbplt_data[0]
        loc_fig = sbplt_data[1]
        axis[a_num]["fig"] = loc_fig
        axs = sbplt_data[2].replace("(", "").replace(")", "").replace(" ", "").split(",")
        if len(sbplt_data) == 4:
            tree = ast.parse(f"f({sbplt_data[3]})")
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
            i += 1
            file.insert(i, spaces + f"_axis[\"default\"][\"geometry\"] = ({controls})\n")
        axis[a_num]["axis"] += axs
        for a in range(len(axs)):
            i += 1
            file.insert(i, spaces + f"_axis[\"{axs[a]}\"]="+"{\"datas\": [], \"cmds\": {}, \"plt_no\": "+ str(a+1) + "}\n")
    else:
        for pn in [plt_name] + axis[a_num]["axis"] + [axis[a_num]["fig"]]:
            if f"{pn}.show()" in file[i] or f"{pn}.savefig(" in file[i]:
                spaces = re.search(r"^([\s\#]*)" + pn + r"\.", file[i]).groups()
                if spaces:
                    spaces = spaces[0]
                else:
                    spaces = ""
                fn = ""
                if f"{pn}.savefig(" in file[i]:
                    fn = file[i].split(".savefig(")[1].split(",")[0].replace("\"", "").replace("\'", "").replace(")", "").strip()
                    fn = ".".join(fn.split(".")[:-1])
                elif r"#name:" in file[i-1]:
                    fn = file[i-1].split(r"#name:")[1].strip()
                nme = pn
                if pn == plt_name: nme = "default"
                file.insert(i-1, spaces + f"_axis[\"{nme}\"][\"names\"] = \"{fn}\"\n")
                i += 2
                file.insert(i, "\n")
                i += 1
                file.insert(i, spaces + f"_axis_list.append(_axis.copy())\n")
                i += 1
                file.insert(i, spaces + "_axis = {\"default\": {\"datas\": [], \"cmds\": {}, \"plt_no\": 0}}\n")
                a_num += 1
                axis[a_num] = {"axis" : [plt_name], "fig": None}
            elif any(f"{pn}.{plttype}" in file[i] for plttype in ["plot", "scatter", "errorbar", "semilogx", "semilogy", "loglog", "stem"]):
                tree = ast.parse(file[i].strip())
                call = tree.body[0].value
                args = [ast.unparse(arg) for arg in call.args]
                kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in call.keywords]
                spaces = list(re.search(r"^([\s\#]*)" + pn + r"\.([\w]+)\(", file[i]).groups())
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
                nme = pn
                if pn == plt_name: nme = "default"
                i += 1
                file.insert(i, spaces + f"_axis[\"{nme}\"][\"datas\"].append([\"{ptype}\", {x}, {y}, {controls}])\n")
            elif f"{pn}.twinx()" in file[i]:
                groups = re.search(r"^([\s\#]*)([a-zA-Z0-9_]+)\s*=\s*" + pn + r"\.twinx\(\s*\)\s*$", file[i])
                if groups:
                    spaces, new_axes = groups.group(1), groups.group(2)
                    axis[a_num]["axis"] += [new_axes]
                    i += 1
                    file.insert(i, spaces + f"_axis[\"{new_axes}\"]="+"{\"datas\": [], \"cmds\": {}, \"plt_no\":" +  f"-_axis[\"{pn}\"][\"plt_no\"]" + "}\n")
            elif f"{pn}." in file[i]:
                groups = re.search(r"^([\s\#]*)" + pn + r"\.([\w]+)\((.*)\)\s*$", file[i])
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
                    nme = pn
                    if pn == plt_name or pn == axis[a_num]["fig"]: nme = "default"
                    i += 1
                    file.insert(i, spaces + f"_axis[\"{nme}\"][\"cmds\"][\"{cmd}\"] = [{controls}]\n")
    i += 1

default_graph_arguments = {}#{"width": "13cm", "height": "10cm"}
dims = (13,10)
file = "".join(file)
namespace = {}
#with open("test_run.py", "w") as f:
#    f.write(str(file))
exec(file, namespace)
axs_list = namespace["_axis_list"]
#with open("test_run.txt", "w") as f:
#    f.write(str(axs_list))
#rcP = namespace[plt_name].rcParams
decimal_sep = OVERRIDE_DECIMAL_SEP
th_sep = "" if OVERRIDE_1000_SEP == "x" else OVERRIDE_1000_SEP
try:
    locale = namespace["locale"].localeconv()
    if not OVERRIDE_DECIMAL_SEP:
        decimal_sep = locale["decimal_point"]
    if OVERRIDE_1000_SEP == "x":
        th_sep = locale["thousands_sep"]
    #default_graph_arguments["xticklabel"] = default_graph_arguments["yticklabel"] = r"{\pgfmathprintnumber[assume math mode=true, 1000 sep={" + th_sep + r"},dec sep={" + decimal_sep + r"}]{\tick} $}"
except: pass
    #if OVERRIDE_DECIMAL_SEP:
    #    default_graph_arguments["xticklabel"] = default_graph_arguments["yticklabel"] = r"{\pgfmathprintnumber[assume math mode=true, dec sep={" + decimal_sep + r"}]{\tick}}"

anchor_map = {"top": "north", "bottom": "south", "upper": "north", "lower": "south", "left": "west", "right": "east", "center": "center"}
legend_pos_map = ["best", "upper right", "upper left", "lower_left", "lower right", "right", "center left", "center right", "lower center", "upper center", "center"]

for plt_num in range(a_num):   # read and parse obtained commands into .tikz file(-s)
    plt = axis[plt_num]
    if len(axs_list) <= plt_num:
        continue
    params = axs_list[plt_num]
    distr = {0: {"pos" : (0,0,1,1)}} # x,y,rel w,rel h
    shape = [1,1]
    if "geometry" in params["default"].keys():
        geom = params["default"]["geometry"]
        args = [geom[q] for q in range(len(geom)) if not isinstance(geom[q], tuple)]
        kwargs = [geom[q] for q in range(len(geom)) if isinstance(geom[q], tuple)]
        for i in range(len(args)):
            shape[i] = args[i]
        nx, ny = int(shape[1]), int(shape[0])
        for x in range(nx):
            for y in range(ny):
                distr[y*nx+x+1] = {"pos": (x,y,1/nx,1/ny)}
        for kw in kwargs:
            k, arg = kw
            if k.strip() == "width_ratios":
                arg = arg.strip("[]()")
                if "," in arg: arg=arg.split(",")
                else: arg=arg.split(" ")
                arg = [float(arg[q]) for q in range(len(arg))]
                s = sum(arg)
                for d in distr.keys():
                    q = distr[d]["pos"]
                    distr[d]["pos"] = (q[0], q[1], arg[q[0]] / s, q[3])
            if k.strip() == "height_ratios":
                arg = arg.strip("[]()")
                if "," in arg: arg=arg.split(",")
                else: arg=arg.split(" ")
                arg = [float(arg[q]) for q in range(len(arg))]
                s = sum(arg)
                for d in distr.keys():
                    q = distr[d]["pos"]
                    distr[d]["pos"] = (q[0], q[1], q[2], arg[q[1]] / s)
#            if "share" in k:
#                if arg.strip() == "row": arg = 1
#                elif arg.strip() == "col": arg = 2
#                elif arg.strip() == "all" or arg.strip() == "True": arg = 0
#                sh_ax = k.strip().removeprefix("share")
#                distr[d][f"{sh_ax}mode"] = arg
    
    for ax_name in plt["axis"]:
        if ax_name == plt_name: ax_name = "default"
        data = params[ax_name]
        cmds = data["cmds"]
        datas = data["datas"]
        plt_no = data["plt_no"]
        legend = False        
        if plt_no < 0:
            distr[abs(plt_no)]["secondary"] = []
        else:
            distr[abs(plt_no)].update({"primary" : [], "labels" : [], "legends": [False, False]})

        def find_def(k, vals):
            output = {}
            try:
                if "lim" in k or k in ["set_xlim", "set_ylim"]:
                    k = k.replace("set_", "")
                    if isinstance(vals[0], tuple):
                        for v in vals:
                            s = str(v[0]).strip().replace("left", "min").replace("bottom", "min").replace("right", "max").replace("top", "max")
                            output[k[0]+s]=v[1]
                    else:
                        sp, zg = str(k).replace("lim", "min"), str(k).replace("lim", "max")
                        if len(vals) == 2:
                            output[sp], output[zg] = vals
                        else:
                            output[sp], output[zg] = vals[0].strip("()").split(", ")
                if "legend" == str(k).strip():
                    global legend
                    legend = True
                    ind = 1 * (plt_no < 0)
                    distr[abs(plt_no)]["legends"][ind] = True
                if str(k) in ["xticks", "yticks"]:
                    tck = str(k).removesuffix("s")
                    tns = ",".join([str(q).strip() for q in str(vals[0]).replace("[", r"{").replace("]", r"}").split(",")])
                    if len(tns) < 3:
                        tns = r"\empty"
                    output[tck] = tns
                    if len(vals) == 2:
                        tls = ",".join([str(q).strip().removeprefix("\'").removesuffix("\'") for q in str(vals[1]).strip("[ ]").split(",")])
                        output[tck + "labels"] = r"{" + tls + r"}"
                elif k == "grid":
                    output[k] = "both"
                elif str(k).strip() == "set_size_inches":
                    w, h = float(vals[0]), float(vals[1])
                    w -= 0.9
                    h -= 1.1
                    w *= 2
                    h *= 2
                    global dims
                    dims = (w, h)
                elif str(k).strip() in ["set_xscale", "set_yscale"]:
                    log_ax = str(k).strip().removeprefix("set_").removesuffix("scale")
                    if vals[0].strip() == "log":
                        base = 10
                        if len(vals) > 1 and isinstance(vals[1], tuple) and vals[1][0].strip() == "base":
                            base = float(vals[1][1])
                        output[f"{log_ax}mode"] = "log"
                        if int(base) - base < 1e-5: base = int(base)
                        output[f"log basis {log_ax}"] = str(base)
                else:
                    for v in vals:
                        if "title" in k:
                            if isinstance(v, tuple):
                                if "loc" in v[0]:
                                    output["title style"] = r"{align=" + v[1] + r"}"
                            else:
                                output["title"] = r"{" + v + r"}"
                        elif str(k).strip() == "set":
                            if str(v[0]).strip() == "title":
                                output["title"] = r"{" + v[1] + r"}"
                        elif str(k).strip() in ["ylabel", "xlabel", "set_xlabel", "set_ylabel"]:
                            k = str(k).strip().removeprefix("set_")
                            if isinstance(v, tuple):
                                if "loc" in v[0]:
                                    output[f"{k} style"] = r"{anchor=" + anchor_map[v[1]] + r"}"
                            else:
                                output[k] = r"{" + v + r"}"
                        elif str(k).strip() == "figure":
                            if v[0].strip() == "figsize":
                                dims = re.search(r"\(\s*(\S+)\s*\,\s*(\S+)\s*\)", v[1])
                                w, h = float(dims.group(1)), float(dims.group(2))
                                if not DIRECT_FIGSIZE:
                                    w -= 0.9
                                    h -= 1.1
                                    w *= 2
                                    h *= 2
                            dims = (w, h)
                        elif "legend" == str(k).strip():
                            if str(v[0]).strip() == "loc":
                                if str(v[1]).strip == "best":
                                    continue
                                if "(" in v[1]:
                                    tup = re.search(r"\(\s*([\d\.]+)\s*,\s*([\d\.]+)\s*\)", v[1]).groups()
                                    if len(tup) == 2:
                                        lx, ly = tup[0], tup[1]
                                    posit = "south west"
                                else:
                                    if len(v[1]) < 3:
                                        try:
                                            v = (v[0],int(v[1]))
                                        except: continue
                                        v = (v[0], legend_pos_map[v[1]])
                                    posit = " ".join([anchor_map[k] for k in anchor_map if k in v[1]])
                                    border = 0.03
                                    lx, ly = 0.5, 0.5
                                    if "north" in posit:
                                        ly = 1 - border
                                    elif "south" in posit:
                                        ly = border
                                    if "west" in posit:
                                        lx = border
                                    elif "east" in posit:
                                        lx = 1 - border                    
                                output["legend style"] = r"{at={(" + f"{lx},{ly}" + r")}, anchor=" + posit + r"},"         
            except Exception as e:   
                print(f"Napaka pri ukazu  {k}:{v}:{e}")    
            return output
        
        gas = default_graph_arguments.copy()
        for cmd in cmds:
            gas.update(find_def(cmd, cmds[cmd]))

        color_map = {'b':'blue', 'g':'teal', 'r':'red', 'c':'cyan', 'm':'magenta', 'y':'yellow', 'k':'black', 'w':'white', "orange":"orange", "green": "green", "cyan":"cyan", "peru": "brown", "lime": "lime", "gray": "gray", "magenta": "magetna", "purple": "violet"}
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
            """if len(p) == 1:
                #export_graph(False, gas_list[count], plots)
                print(gas_list[count], plots)
                plots = ""
                continue"""
            label = ""
            ptype = p.pop(0)
            style = []
            mark_size = -1
            mark = ""
            ad_col = {}
            xfe, yfe = 0, 0
            for arg in p[2:]:
                try:
                    if isinstance(arg, tuple):
                        k, v = str(arg[0]).strip(), arg[1]
                        if "label" in k:
                            label = v
                        elif "alpha" in k:
                            style.append(f"opacity={v}")
                        elif "marker" == k:
                            marker = next((marker_map[m] for m in arg if m in marker_map), "*")
                            if "." in str(arg) and mark_size == -1:
                                mark_size = 1 
                            mark = marker
                        elif "linewidth" in k:
                            style.append(f"line width={v}pt")
                        elif "linestyle" in k:
                            if v == "":
                                style.append("only marks")
                            elif v in line_map.keys():
                                style.append(line_map[v])
                            elif v in line_map.values():
                                style.append(v)
                        elif "markersize" in k:
                            mark_size = f"{v/2:.f}"
                        elif "color" in k:
                            if v in color_map.keys():
                                col = color_map[v]
                            elif v in color_map.values():
                                col = v
                            elif str(v).strip()[0] == "#":
                                try:
                                    col = hex_to_pgf(v)
                                except:
                                    print("Bad color:", v)
                            else:
                                c = list(str(v).strip("( )").split(", "))
                                while len(c) < 3:
                                    c.append(c[0])
                                col = r"{rgb:" + f"red,{float(c[0])*255:.2f};green,{float(c[1])*255:.2f};blue,{float(c[2])*255:.2f}" + r"}"
                        elif "err" in k:
                            ax = k[0]
                            try:
                                if ax == "x":
                                    xfe = float(v)
                                elif ax == "y":
                                    yfe = float(v)
                            except:
                                subs = v.strip("[]").split("], [")
                                if len(subs) == 1:
                                    descriptor = f"{ax} error"
                                    if "," in subs[0]:
                                        ad_col[descriptor] = subs[0].split(",")
                                    else:
                                        ad_col[descriptor] = subs[0].split()
                                else:
                                    descriptor = f"{ax} error minus"
                                    if "," in subs[0]:
                                        ad_col[descriptor] = subs[0].split(",")
                                    else:
                                        ad_col[descriptor] = subs[0].split()
                                    descriptor = f"{ax} error plus"
                                    if "," in subs[1]:
                                        ad_col[descriptor] = subs[1].split(",")
                                    else:
                                        ad_col[descriptor] = subs[1].split()

                    else:
                        if arg in color_map.values():
                            color = arg
                            marker = False
                        else:
                            color = next((color_map[c] for c in arg if c in color_map), None)
                            marker = next((marker_map[m] for m in arg if m in marker_map), None)
                        if "." in str(marker) and mark_size == -1:
                            mark_size = 1 
                        line = next((line_map[m] for m in line_map if m in arg), None)
                        if color:
                            col = color
                        if marker:
                            mark = marker
                        if line:
                            style.append(f"{line}")
                except Exception as e:
                    print(f"Napaka pri ukazu  {ptype}:{arg}:{e}")

            if mark:
                style.append(f"mark={mark}")
                if mark_size == -1:
                    mark_size = 2
                style.append(f"mark size={mark_size} pt")
            if col == None:
                col = hex_to_pgf(default_colors[len(dci)]) # ALTN: dci.count(ptype)
                dci.append(ptype)
            style.append(f"color={col}")
            if ptype == "scatter":
                style.append("only marks")
            if ptype == "errorbar":
                error_string = r"error bars/.cd," + "\n"
                error_string += f"x dir=both, x fixed={xfe},\n" if xfe else "x dir=both, x explicit,\n"  
                error_string += f"x dir=both, y fixed={yfe},\n" if yfe else "y dir=both, y explicit,"  
                style.append(error_string)
            if "semilog" in ptype:
                log_ax = ptype.strip().replace("semilog", "")
                gas[f"{log_ax}mode"] = "log"
                gas[f"log basis {log_ax}"] = str(10)
                #graph_arguments += f"{log_ax}mode=log, log basis {log_ax} = 10,\n"
            if ptype == "loglog":                
                gas[f"xmode"] = "log"
                gas[f"log basis x"] = str(10)
                gas[f"ymode"] = "log"
                gas[f"log basis y"] = str(10)
            if ptype == "stem":
                style.append("ycomb")
            if len(label) > 0:
                if legend:
                    plots += f"\\addlegendentry{{{label}}}"
                else:
                    plots += f"\\label{{{label}}}"
                    distr[abs(plt_no)]["labels"].append((label, plt_no < 0))
            else:
                style.append("forget plot")
            style = ",\n".join(style)
            x = ["x"] + list(p[0])
            y = ["y"] + list(p[1])
            plot_points = [x,y]
            ad_spec = ""
            for ac in ad_col.keys():
                ad_spec += f", {ac}={ac.replace(" ", "")}"
                pts = [ac.replace(" ", "")] + list(ad_col[ac])
                plot_points.append(pts)
            plots += f"\n\\addplot [{style}] table [x=x,y=y{ad_spec}] {{\n"
            for i in range(len(x)):
                for j in range(len(plot_points)):
                    try:
                        plots += "\t" + str(plot_points[j][i])
                    except:
                        plots += "\t"
                plots += "\n"
            plots += "};\n"

        graph_arguments = r"""/pgf/number format/.cd,""" + "\n"
        if decimal_sep == ",":
            graph_arguments += "use comma,\n"
        graph_arguments += r"1000 sep={"+ th_sep + r"}," + "\n"
        for ga in gas:
            graph_arguments += f"\t{ga}={gas[ga]},\n"
        graph_arguments = graph_arguments.removesuffix(",\n")

        if plt_no < 0:
            distr[abs(plt_no)]["secondary"] = [graph_arguments,plots]
        else:
            distr[abs(plt_no)]["primary"] = [graph_arguments, plots]

    # put it together
    tikz_code = r"\begin{tikzpicture}" + "\n"
    if len(distr.keys()) > 1:
        del(distr[0])
    for d in list(sorted(distr.keys())):
        x, y, w, h = distr[d]["pos"]
        w *= dims[0]
        h *= dims[1]
        pos = ""
        if x == 0:
            if y > 0:
                y -= 1
                neigh = f"p{y*int(shape[1])+x+1}"
                pos = r"at={("+neigh+r".south)}, anchor=north, yshift=-2.5cm," + "\n"
        else:
            x -= 1
            neigh = f"p{y*int(shape[1])+x+1}"
            pos = r"at={("+neigh+r".east)}, anchor=west, xshift=2.5cm," + "\n"
        if "primary" in distr[d].keys():
            dual = "secondary" in distr[d].keys()
            tikz_code += r"\begin{axis}["+ "\n"
            tikz_code += pos
            tikz_code += f"name=p{d},\n"
            tikz_code += f"width={w}cm, height={h}cm,\n"
            if dual:
                tikz_code += r"axis y line*=left," + "\n"
            tikz_code += distr[d]["primary"][0] + "]\n"
            tikz_code += distr[d]["primary"][1] + "\n"
            for l in distr[d]["labels"]:
                lab, sec = l
                if sec and distr[d]["legends"][0]:
                    tikz_code += r"\addlegendimage{/pgfplots/refstyle=" + lab + r"}\addlegendentry{" + lab + "},\n"
            tikz_code += r"\end{axis}" + "\n"
            if dual:
                tikz_code += r"\begin{axis}["+ "\n"
                tikz_code += f"width={w}cm, height={h}cm,\n"
                tikz_code += r"axis y line*=right, axis x line=none," + "\n"
                tikz_code += r"at={(" + f"p{d}" +r".south west)}, anchor=south west, y label style={at={(1.1,0.5)}, rotate=180},"
                tikz_code += distr[d]["secondary"][0] + "]\n"
                for l in distr[d]["labels"]:
                    lab, sec = l
                    if not sec and distr[d]["legends"][1]:
                        tikz_code += r"\addlegendimage{/pgfplots/refstyle=" + lab + r"}\addlegendentry{" + lab + "},\n"
                tikz_code += distr[d]["secondary"][1] + "\n"
                tikz_code += r"\end{axis}" + "\n"
    tikz_code += r"\end{tikzpicture}"
    fn = params["default"]["names"]
    if fn:
        fn = os.path.join(os.path.dirname(path), fn + ".tikz")
    else:
        fn = path.replace(".py", f"{plt_num}.tikz")
    with open(fn, "w") as f:
        f.write(tikz_code)

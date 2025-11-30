# v0.7 development

import re
import ast      # pip install astor
import os
import math


# ================ SETTINGS ================
FILE_PATH = ""              # if emtpy, terminal will ask you for .py to convert
EXPORT_DATAPOINTS = False   # store coordinate tables in separate .dat file(-s) instead of storing them in main .tikz file(-s)
DATAPOINTS_DIR = ""         # location of .dat file(-s) relative to FILE_PATH, also the path for imshow() image saving
DATA_ONLY = False           # change only datapoints - as exported (requires EXPORT_ DATAPOINTS = True, should be used only to update data, which was already exported, will not create/modify .tikz file with plot settings). This option is meant for updating the data while keeping manual changes to the plot settings in .tikz file

OVERRIDE_DECIMAL_SEP = ","  # leave empty for auto
OVERRIDE_1000_SEP = ""      # use x for auto
DIRECT_FIGSIZE = False      # use number of inch in matplotlib as number of cm in LaTeX
DEFUALT_FIGSIZE = (13,10)   # default size setting in cm
LEGEND_REL_X = 0.03         # relative padding from axis
LEGEND_REL_Y = 0.03
TITLE_CM = 0.75             # added padding between subplots if title is present
AX_LABEL_X_CM = 0.6         # x-label added padding
AX_TICKS_X_CM = 0.5         # x-axis ticks added padding
AX_LABEL_Y1_CM = 0.6        # primary y-label added padding
AX_TICKS_Y1_CM = 1          # primary y-ticks added padding
AX_LABEL_Y2_CM = 0.6        # secondary y-label added padding
AX_TICKS_Y2_CM = 1          # secondary y-ticks added padding
PLOT_AUTOPAD = 0.03         # percent of axis extended when shared axis are used and limit is not specified

DEV_MODE = False

# ================ READ/PARSE CODE ================
if DEV_MODE: import traceback

file = []
path = FILE_PATH
if path:
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

file.insert(0, "_axis = {\"default\": {\"datas\": [], \"cmds\": {}, \"plt_no\": 0}}\n_axis_list={}\n")
i = 0
plt_name = ""
axis = {}
a_num = 0
imshow_count = 0
while not plt_name and i < len(file):
    if "import matplotlib.pyplot" in file[i]:
        q = file[i].split(" as ")
        plt_name = q[1].strip()
        axis = {0: {"axis" : [plt_name], "fig": None}}
    i += 1
while i < len(file):
    strpd = file[i].strip()
    if len(strpd) == 0 or strpd[0] == "#":
        i += 1
        continue
    if "def " in file[i].lstrip():
        qi = 1
        while file[i+qi].lstrip() in ["#", "r\"", "\"",] or len(file[i+qi].strip()) < 1:
            qi += 1
        indent = file[i+qi][:len(file[i+qi]) - len(file[i+qi].lstrip())]
        file.insert(i+1, indent + "global _axis\n")
        file.insert(i+2, indent + "global _axis_list\n")
        i += 2
    if f"{plt_name}.subplots" in file[i]:
        sbplt_data = list(re.search(r"^([\s\#]*)([a-zA-Z0-9_]*),(.*)=\s*" + plt_name + r"\.subplots\((.*)\)\s*$", file[i]).groups())
        spaces = sbplt_data[0]
        loc_fig = sbplt_data[1]
        axis[a_num]["fig"] = loc_fig
        nr = nc = 1
        if len(sbplt_data) == 4:
            tree = ast.parse(f"f({sbplt_data[3]})")
            call=tree.body[0].value
            args = [ast.unparse(arg) for arg in call.args]
            kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in call.keywords]
            controls = ""
            for na in range(len(args)):
                arg = args[na]
                controls += f"str({arg}), "
                if na == 0:
                    nr = int(arg)
                elif na == 1:
                    nc = int(arg)
            for kwarg in kwargs:
                spl = kwarg.split("=")
                k, v = spl[0], "=".join(spl[1:])
                if "nrows" in k:
                    nr = int(v)
                elif "ncols" in k:
                    nc = int(v)
                controls += f"(\"{k}\", str({v})), "
            controls = controls.removesuffix(", ")
            i += 1
            file.insert(i, spaces + f"_axis[\"default\"][\"geometry\"] = ({controls})\n")
        ax_ref = sbplt_data[2]
        depth = 0
        current = ""
        grid = {}
        x,y=0,0
        for a in ax_ref:
            if a == "(":
                depth += 1
                x=0
            elif a == ")":
                if current:
                    if y not in grid:
                        grid[y] = {}
                    grid[y][x] = current
                    current = ""
                depth -= 1
                x=0
            elif a == ",":
                if current:
                    if y not in grid:
                        grid[y] = {}
                    grid[y][x] = current
                    current = ""
                if depth == 1:
                    y += 1
                elif depth == 2:
                    x += 1
            elif a != " ":
                current += a
        axs = []
        if grid:
            if len(grid.keys()) == nr:
                for y in grid.keys():                    
                    prva = grid[y][0]
                    if len(grid[y].keys()) == nc:
                        for x in grid[y].keys():
                            axs.append(grid[y][x])
                    elif prva and prva.strip() != "_":
                        for x in range(nc):
                            axs.append(prva + f"[{x}]")
            elif len(grid.keys()) == nc:
                pass
        else:
            if nr * nc == 1:
                axs = sbplt_data[2].replace("(", "").replace(")", "").replace(" ", "").split(",")
            else:
                for y in range(nr):
                    if nc > 1:
                        for x in range(nc):
                            axs.append(sbplt_data[2].split(",")[0].strip("[ ]") + f"[{y}][{x}]")
                    else:
                        axs.append(sbplt_data[2].split(",")[0].strip("[ ]") + f"[{y}]")
        if not axs:
            axs = sbplt_data[2].replace("(", "").replace(")", "").replace(" ", "").split(",")
        axis[a_num]["axis"] += axs
        for a in range(len(axs)):
            i += 1
            file.insert(i, spaces + f"_axis[\"{axs[a]}\"]="+"{\"datas\": [], \"cmds\": {}, \"plt_no\": "+ str(a+1) + "}\n")
    else:
        if "." in file[i]:
            row_name = file[i].split(".")[0].lstrip()
            nme = row_name.split("[")[0]
            indexs = ""
            if "[" in row_name:
                brackets = row_name.split("[")[1:]
                for b in brackets:
                    b = b.removesuffix("]")
                    indexs += f"[{{{b}}}]"

            row_cmd = file[i].split(".")[1].split("(")[0]

            if row_cmd in ["show", "savefig"]:
                spaces = re.search(r"^([\s\#]*)" + re.escape(row_name) + r"\.", file[i]).groups()
                if spaces:
                    spaces = spaces[0]
                else:
                    spaces = ""
                fn = ""
                if f"{row_name}.savefig(" in file[i]:
                    fn = file[i].split(".savefig(")[1].split(",")[0].replace("\"", "").replace("\'", "").replace(")", "").strip()
                    fn = ".".join(fn.split(".")[:-1])
                elif r"#name:" in file[i-1]:
                    fn = file[i-1].split(r"#name:")[1].strip()
                if row_name == plt_name: nme = "default"
                i += 1
                file.insert(i-1, spaces + f"_axis[f\"{nme + indexs}\"][\"names\"] = \"{fn}\"\n")
                i += 1
                file.insert(i, "\n")
                i += 1
                file.insert(i, spaces + f"_axis_list[{a_num}] = _axis.copy()\n")
                i += 1
                file.insert(i, spaces + "_axis = {\"default\": {\"datas\": [], \"cmds\": {}, \"plt_no\": 0}}\n")
                a_num += 1
                axis[a_num] = {"axis" : [plt_name], "fig": None}
            elif row_cmd == "imshow":
                tree = ast.parse(file[i].strip())
                call = tree.body[0].value
                args = [ast.unparse(arg) for arg in call.args]
                kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in call.keywords]
                spaces = list(re.search(r"^([\s\#]*)" + re.escape(row_name) + r"\.([\w]+)\(", file[i]).groups())
                ptype = spaces[-1]
                if len(spaces) == 2:
                    spaces = spaces[0]
                else:
                    spaces = ""
                controls = ""
                x = args.pop(0)
                for arg in args:
                    controls += f"str({arg}), "
                for kwarg in kwargs:
                    spl = kwarg.split("=")
                    k, v = spl[0], "=".join(spl[1:])
                    controls += f"(\"{k}\", str({v})), "
                controls = controls.removesuffix(", ")
                if row_name == plt_name: nme = "default"
                i += 1
                file.insert(i, spaces + re.escape(row_name) + ".axis(\"off\")\n")
                i += 1
                im_dir = os.path.join(FILE_PATH, DATAPOINTS_DIR)
                if im_dir:
                    os.makedirs(im_dir, exist_ok=True)
                im_show_path = os.path.join(FILE_PATH, DATAPOINTS_DIR, f"imshow{imshow_count}.pdf")
                file.insert(i, spaces + re.escape(row_name) + f".savefig(\"{im_show_path}\", bbox_inches=\"tight\", pad_inches=0)\n")
                tree = ast.parse(file[i].strip())
                call = tree.body[0].value
                args = [ast.unparse(arg) for arg in call.args]
                kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in call.keywords]
                i += 1
                file.insert(i, spaces + f"_axis[f\"{nme + indexs}\"][\"datas\"].append([\"{ptype}\", [len({x}), len({x}[0])], {controls}, \"{im_show_path}\"])\n")
                imshow_count += 1
            elif row_cmd in ["plot", "scatter", "errorbar", "semilogx", "semilogy", "loglog", "stem", "bar"]:
                tree = ast.parse(file[i].strip())
                call = tree.body[0].value
                args = [ast.unparse(arg) for arg in call.args]
                kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in call.keywords]
                spaces = list(re.search(r"^([\s\#]*)" + re.escape(row_name) + r"\.([\w]+)\(", file[i]).groups())
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
                if nme == plt_name: nme, indexs = "default", ""
                file.insert(i, spaces + f"_axis[f\"{nme + indexs}\"][\"datas\"].append([\"{ptype}\", {x}, {y}, {controls}])\n")
                i += 1
            elif row_cmd in ["vlines", "hlines", "axvline", "axhline"]:
                tree = ast.parse(file[i].strip())
                call = tree.body[0].value
                args = [ast.unparse(arg) for arg in call.args]
                kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in call.keywords]
                spaces = list(re.search(r"^([\s\#]*)" + re.escape(row_name) + r"\.([\w]+)\(", file[i]).groups())
                ptype = spaces[-1]
                if len(spaces) == 2:
                    spaces = spaces[0]
                else:
                    spaces = ""
                controls = ""
                for arg in args:
                    controls += f"str({arg}), "
                for kwarg in kwargs:
                    spl = kwarg.split("=")
                    k, v = spl[0], "=".join(spl[1:])
                    controls += f"(\"{k}\", str({v})), "
                controls = controls.removesuffix(", ")
                if row_name == plt_name: nme = "default"
                file.insert(i, spaces + f"_axis[f\"{nme + indexs}\"][\"datas\"].append([\"{ptype}\", {controls}])\n")
                i += 1
            elif row_cmd == "twinx":
                groups = re.search(r"^([\s\#]*)([a-zA-Z0-9_]+)\s*=\s*(\S+)\.twinx\(\s*\)\s*$", file[i])
                if groups:
                    spaces, new_axes, row_nm = groups.group(1), groups.group(2), groups.group(3)
                    row_name = file[i].split(".")[0].lstrip()
                    nme = row_nm.split("[")[0]
                    indexs = ""
                    if "[" in row_nm:
                        brackets = row_name.split("[")[1:]
                        for b in brackets:
                            b = b.removesuffix("]")
                            indexs += f"[{{{b}}}]"

                    axis[a_num]["axis"] += [new_axes]
                    file.insert(i, spaces + f"_axis[\"{new_axes}\"]="+"{\"datas\": [], \"cmds\": {}, \"plt_no\":" +  f"-_axis[f\"{nme + indexs}\"][\"plt_no\"]" + "}\n")
                    i += 1
            else:
                checked_names = []
                for nm in [plt_name] + axis[a_num]["axis"] + [axis[a_num]["fig"]]:
                    if not nm: continue
                    nm = nm.split("[")[0]
                    if nm in checked_names: continue
                    else: checked_names.append(nm)
                    if nm != nme: continue
                    groups = re.search(r"^([\s\#]*)" + re.escape(row_name) + r"\.([\w]+)\((.*)\)\s*$", file[i])
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
                        if row_name == plt_name or row_name == axis[a_num]["fig"]: nme = "default"
                        file.insert(i, spaces + f"_axis[f\"{nme + indexs}\"][\"cmds\"][\"{cmd}\"] = [{controls}]\n")
                        i += 1
    i += 1

default_graph_arguments = {}#{"width": "13cm", "height": "10cm"}
dims = DEFUALT_FIGSIZE
file = "".join(file)
namespace = {"__name__": "__main__", "__builtins__": __builtins__}
if DEV_MODE:
    with open("test_run.py", "w") as f:
        f.write(str(file))
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
    dat_count = 0
    lab_count = 0
    plt = axis[plt_num]
    limit_names = ["xmin", "xmax", "ymin", "ymax"]
    limits = { axnm: [None,None,None,None] for axnm in plt["axis"]}
    xshare, yshare = -1, -1
    ax_v_def, ax_h_def = False, False
    if plt_num in axs_list.keys():
        params = axs_list[plt_num]
    else:
        continue
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
            if "share" in k:
                if arg.strip() == "row": arg = 1
                elif arg.strip() == "col": arg = 2
                elif arg.strip() == "all" or arg.strip() == "True": arg = 0
                else: arg = -1
                if k.strip().removeprefix("share") == "x": xshare = arg
                else: yshare = arg
    for ax_name in plt["axis"]:
        if ax_name == plt_name: ax_name = "default"
        data = params[ax_name]
        cmds = data["cmds"]
        datas = data["datas"]
        plt_no = data["plt_no"]
        xmin = ymin = float("inf")
        xmax = ymax = float("-inf")
        vlines = []
        hlines = []
        legend = False        
        if plt_no < 0:
            distr[abs(plt_no)]["secondary"] = []
        else:
            distr[abs(plt_no)].update({"primary" : [], "labels" : {}, "legends": [False, False], "borders": [0,0,0,0]}) # borders: 0-left, 1-bottom, ...

        def find_def(k, vals):
            output = {}
            try:
                if "lim" in k or k in ["set_xlim", "set_ylim"]:
                    k = k.replace("set_", "")
                    if isinstance(vals[0], tuple):
                        for v in vals:
                            s = str(v[0]).strip().replace("left", "min").replace("bottom", "min").replace("right", "max").replace("top", "max")
                            output[k[0]+s]=v[1]
                            if ax_name != "default":
                                limits[ax_name][limit_names.index(k[0]+s)] = v[1]
                    else:
                        sp, zg = str(k).replace("lim", "min"), str(k).replace("lim", "max")
                        if len(vals) == 2:
                            output[sp], output[zg] = vals
                        else:
                            output[sp], output[zg] = vals[0].strip("()").split(", ")
                        if ax_name != "default":
                            limits[ax_name][limit_names.index(sp)] = output[sp]
                            limits[ax_name][limit_names.index(zg)] = output[zg]
                if "legend" == str(k).strip():
                    global legend
                    legend = True
                    ind = 1 * (plt_no < 0)
                    distr[abs(plt_no)]["legends"][ind] = True
                if str(k) in ["xticks", "yticks", "set_xticks", "set_yticks"]:
                    tck = str(k).removesuffix("s").removeprefix("set_")
                    tns = ",".join([str(q).strip() for q in str(vals[0]).replace("[", r"{").replace("]", r"}").split(",")])
                    if len(tns) < 3:
                        tns = r"\empty"
                    output[tck] = tns
                    if len(vals) == 2:
                        tls = ",".join([str(q).strip().removeprefix("\'").removesuffix("\'") for q in str(vals[1]).strip("[ ]").split(",")])
                        output[tck + "labels"] = r"{" + tls + r"}"
                elif str(k) in ["set_xticklabels", "set_yticklabels"]:
                    axis = str(k).removeprefix("set_").removesuffix("ticklabels")
                    if len(vals) == 1:
                        if len(vals[0]) < 3:
                            output[f"{axis}ticklabel"]=r"\empty"
                        else:
                            tcks = vals[0].replace("\'", "").replace("\"", "").strip("[]").split(", ")
                            output[f"{axis}ticklabel"] = r"{" + ",".join(tcks) + r"}"                       
                elif k == "grid":
                    output[k] = "both"
                elif str(k).strip() == "set_size_inches":
                    global dims
                    w, h = float(vals[0]), float(vals[1])
                    if not DIRECT_FIGSIZE:
                        w -= 0.9
                        h -= 1.1
                        w *= 2
                        h *= 2
                    dims = (w, h)
                elif str(k).strip() in ["set_xscale", "set_yscale", "xscale", "yscale"]:
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
                                    if "center" in posit:
                                        if "north" in posit or "south" in posit or "west" in posit or "east" in posit:
                                            posit = posit.replace("center", "")
                                    lx, ly = 0.5, 0.5
                                    if "north" in posit:
                                        ly = 1 - LEGEND_REL_Y
                                    elif "south" in posit:
                                        ly = LEGEND_REL_Y
                                    if "west" in posit:
                                        lx = LEGEND_REL_X
                                    elif "east" in posit:
                                        lx = 1 - LEGEND_REL_X                  
                                output["legend style"] = r"{at={(" + f"{lx},{ly}" + r")}, anchor=" + posit + r"},"         
            except Exception as e:   
                print(f"Napaka pri ukazu  {k}:{e}")
                if DEV_MODE: print(traceback.format_exc())   
            return output
        
        gas = default_graph_arguments.copy()
        for cmd in cmds:
            gas.update(find_def(cmd, cmds[cmd]))

        color_map = {'b':'blue', 'g':'teal', 'r':'red', 'c':'cyan', 'm':'magenta', 'y':'yellow', 'k':'black', 'w':'white', "orange":"orange", "green": "green", "cyan":"cyan", "peru": "brown", "lime": "lime", "gray": "gray", "magenta": "magetna", "purple": "violet"}
        marker_map = {'o':'*', ".": "*", 's':'square*', '^':'triangle', 'v':'triangle*', 'd':'diamond', '+':'+', 'x':'x', '*':'star'}
        line_map = {"--": "dashed", ":": "dotted", "-.": "dashdotted"}
        default_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
        dci = []

        def hex_to_pgf(hex):
            c = []
            for i in [1,3,5]:
                c.append(int(hex[i:i+2], 16) / 255)
            return r"{rgb:" + f"red,{c[0]:.2f};green,{c[1]:.2f};blue,{c[2]:.2f}" + r"}"

        plots = []
        plot = ""
        while datas:
            col = None
            p = datas.pop(0)
            label = ""
            ptype = p.pop(0)
            style = []
            mark_size = -1
            mark = ""
            stem_horizontal = False
            ad_col = {}
            xfe, yfe = 0, 0
            cline = ptype in ["vlines", "hlines", "axvline", "axhline"]
            num_args = 2
            if ptype in ["axvline", "axhline"]: num_args = 1
            if ptype == "imshow":
                gas.update({"enlargelimits": "false"})
                imshow_num = p.pop()
                shape = p.pop(0)
                bounds = [0, shape[1], 0, shape[0]]
                for arg in p:
                    if arg[0] == "extent":
                        exts = arg[1].strip("[]")
                        if "," in exts: bounds = exts.split(",")
                        else: bounds = exts.split()
                        xm, xM, ym, yM = bounds
                        if "ymode" in gas and gas["ymode"]=="log":
                            if float(ym) <= 0: ym = 1
                        if "xmode" in gas and gas["xmode"]=="log":
                            if float(xm) <= 0: xm = 1
                for l in range(len(limit_names)):
                    if limit_names[l] not in gas:
                        gas[limit_names[l]] = bounds[l]
                    else:
                        bounds[l] = gas[limit_names[l]]
                xm, xM, ym, yM = bounds
                plot += r"\addplot graphics[" + "\n"
                plot += f"xmin={xm}, xmax={xM}, ymin={ym}, ymax={yM},\n"
                plot += r"] {" + imshow_num + r"};" + "\n"
                
                plots.append(plot)             
                continue
            for arg in p[num_args:]:
                if isinstance(arg, list): continue
                try:
                    fmt_set = None
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
                        elif "linewidth" in k or k == "lw":
                            style.append(f"line width={v}pt")
                        elif "linestyle" in k or k == "ls":
                            if v == "" or "None" in v or "none" in v:
                                style.append("only marks")
                            elif v in line_map.keys():
                                style.append(line_map[v])
                            elif v in line_map.values():
                                style.append(v)
                        elif "markersize" in k or k == "ms":
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
                        elif "fmt" in k:
                            if v == "none":
                                mark=""
                                style.append("draw=none")
                            else:
                                fmt_set = v
                        elif "width" in k and ptype == "bar":
                            gas.update({"enlargelimits": "false"})
                            style.append(f"bar width={str(v)}")
                        elif "orientation" in k and ptype == "stem":
                            if "horizontal" in v:
                                stem_horizontal = True
                        if fmt_set == None:
                            continue
                    if fmt_set: arg = fmt_set
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
            if ptype == "bar":
                style.insert(0, f"fill={col}")
            style.append(f"color={col}")
            if ptype == "scatter":
                style.append("only marks")
            if ptype == "errorbar":
                error_string = r"error bars/.cd," + "\n"
                error_string += r"error bar style={solid},"+"\n"
                error_string += f"x dir=both, x fixed={xfe},\n" if xfe else "x dir=both, x explicit,\n"  
                error_string += f"y dir=both, y fixed={yfe},\n" if yfe else "y dir=both, y explicit,"
                style.append(error_string)
            elif "semilog" in ptype:
                log_ax = ptype.strip().replace("semilog", "")
                gas[f"{log_ax}mode"] = "log"
                gas[f"log basis {log_ax}"] = str(10)
                #graph_arguments += f"{log_ax}mode=log, log basis {log_ax} = 10,\n"
            elif ptype == "loglog":                
                gas[f"xmode"] = "log"
                gas[f"log basis x"] = str(10)
                gas[f"ymode"] = "log"
                gas[f"log basis y"] = str(10)
            elif ptype == "stem":
                if stem_horizontal:
                    style.append("xcomb")
                else:
                    style.append("ycomb")
            elif ptype in ["vlines", "hlines"]:
                s = 0
                while s < len(style):
                    if "mark" in style[s]: style.pop(s)
                    else: s+= 1
                lines = []
                vert = "v" in ptype
                for q in range(3):
                    linep = p[q]
                    linep = linep.strip("[]")
                    if "," in linep: linep = linep.split(", ")
                    else: linep = linep.split(" ")
                    lines.append(linep)
                while len(lines[1]) < len(lines[0]):
                    lines[1].append(lines[1][-1])
                while len(lines[2]) < len(lines[0]):
                    lines[2].append(lines[2][-1])
                if not label:
                    style.insert(0,"forget plot")
                for q in range(len(lines[0])):
                    points = ""
                    if vert:
                        points = f"{float(lines[0][q]), float(lines[1][q])}\n{float(lines[0][q]), float(lines[2][q])}"
                    else:
                        points = f"{float(lines[1][q]), float(lines[0][q])}\n{float(lines[2][q]), float(lines[0][q])}"
                    if q > 0: 
                        style.insert(0,"forget plot")
                        style =list(set(style))
                        plots.append(f"\n\\addplot[{",".join(style)}] coordinates {{{points}}};")
                    else: plots.append(f"\n\\addplot[{",".join(style)}] coordinates {{{points}}};")
                if len(label) > 0:
                    if legend:
                        plots[-1] += f"\\addlegendentry{{{label}}}"
                    else:
                        plots[-1] += f"\\label{{lab{lab_count}}}"
                        distr[abs(plt_no)]["labels"][lab_count] = (label, plt_no < 0)
                        lab_count += 1
                
            elif ptype in ["axvline", "axhline"]:
                arbit = [0,0,1]
                #style.append("forget plot")
                for q in range(len(p)):
                    if isinstance(p[q], tuple):
                        if p[q][0] in ["x", "y"]:
                            arbit[0] = p[q][1]
                        elif p[q][0] in ["xmin", "ymin"]:
                            arbit[1] = p[q][1]
                        elif p[q][0] in ["xmax", "ymax"]:
                            arbit[2] = p[q][1]
                    else:
                        arbit[q] = p[q]
                if "v" in ptype:
                    plots.append(f"\n\\DrawVline{{{arbit[0]}}}{{{arbit[1]}}}{{{arbit[2]}}}{{{",".join(style)}}}")
                    ax_v_def = True
                else:
                    plots.append(f"\n\\DrawHline{{{arbit[0]}}}{{{arbit[1]}}}{{{arbit[2]}}}{{{",".join(style)}}}")
                    ax_h_def = True
                if len(label) > 0:
                    if legend:
                        plots[-1] += f"\\addlegendimage{{{", ".join(style)}}}\\addlegendentry{{{label}}}"
            elif ptype == "bar":
                style.insert(0, "ybar")
            legend_entry_command = ""
            if len(label) > 0 and not cline:
                if legend:
                    legend_entry_command = f"\\addlegendentry{{{label}}}"
                else:
                    legend_entry_command = f"\\label{{lab{lab_count}}}"
                    distr[abs(plt_no)]["labels"][lab_count] = (label, plt_no < 0)
                    lab_count += 1
            elif not cline:
                style.insert(0,"forget plot")
            style = ",\n".join(style)
            if not cline:
                x = ["x"] + list(p[0])
                y = ["y"] + list(p[1])
                plot_points = [x,y]
                ad_spec = ""
                for ac in ad_col.keys():
                    ad_spec += f", {ac}={ac.replace(" ", "")}"
                    pts = [ac.replace(" ", "")] + list(ad_col[ac])
                    plot_points.append(pts)
                plot += f"\n\\addplot [{style}] table [x=x,y=y{ad_spec}] {{"
                content = ""
                for i in range(len(x)):
                    line = ""
                    valid = True
                    for j in range(len(plot_points)):
                        try:
                            pp = plot_points[j][i]
                            line += "\t" + str(pp)
                            if pp in ["NaN", None, "None"]:
                                valid = False
                            if i > 0:
                                if j == 0:
                                    xmin = min(xmin, pp)
                                    xmax = max(xmax, pp)
                                elif j == 1:
                                    ymin = min(ymin, pp)
                                    ymax = max(ymax, pp)
                        except Exception as e:
                            print(f"Bad value: {pp}, ignoring. Error: {e}")
                            content += "\t"
                    if valid:
                        content += line + "\n"
                if EXPORT_DATAPOINTS:
                    fn = params["default"]["names"]
                    if not fn:
                        fn = fn.split("/")[-1]
                        fn = path.replace(".py", f"{plt_num}")
                    fn += f"_tikzplot_dat{dat_count}.dat"                    
                    dat_file = os.path.join(FILE_PATH, DATAPOINTS_DIR)
                    if dat_file:
                        os.makedirs(dat_file, exist_ok=True)
                    dat_file = os.path.join(dat_file, fn)
                    plot += dat_file
                    with open(dat_file, "w") as dat:
                        dat.write(content)
                    dat_count += 1
                else:
                    plot += "\n" + content
                plot += "};\n" + legend_entry_command
                plots.append(plot)
                plot = ""
        if ax_name != "default":
            if xshare >= 0:
                if "xmin" not in gas:
                    limits[ax_name][0] = f"d{xmin}"
                if "xmax" not in gas:
                    limits[ax_name][1] = f"d{xmax}"
                s_num = ""
                if xshare == 1:
                    s_num = distr[abs(plt_no)]["pos"][1]
                elif xshare == 2:
                    s_num = distr[abs(plt_no)]["pos"][0]
                gas["xmin"] = r"\xmin"
                gas["xmax"] = r"\xmax"
                if xshare > 0:
                    gas["xmin"] = r"\xmin" + chr(97+s_num)
                    gas["xmax"] = r"\xmax" + chr(97+s_num)
            if yshare >= 0:
                if "ymin" not in gas:
                    limits[ax_name][2] = f"d{ymin}"
                if "ymax" not in gas:
                    limits[ax_name][3] = f"d{ymax}"
                s_num = ""
                if yshare == 1:
                    s_num = distr[abs(plt_no)]["pos"][1]
                elif yshare == 2:
                    s_num = distr[abs(plt_no)]["pos"][0]
                gas["ymin"] = r"\ymin"
                gas["ymax"] = r"\ymax"
                if yshare > 0:
                    gas["ymin"] = r"\ymin" + chr(97+s_num)
                    gas["ymax"] = r"\ymax" + chr(97+s_num)
        graph_arguments = r"""/pgf/number format/.cd,""" + "\n"
        if decimal_sep == ",":
            graph_arguments += "use comma,\n"
        graph_arguments += r"1000 sep={"+ th_sep + r"}," + "\n"
        for ga in gas:
            graph_arguments += f"\t{ga}={gas[ga]},\n"
        graph_arguments = graph_arguments.removesuffix(",\n")
        plots = "".join(plots)
        if plt_no < 0:
            distr[abs(plt_no)]["secondary"] = [graph_arguments,plots]
            if "ylabel" in gas and gas["ylabel"]:
                distr[abs(plt_no)]["borders"][2] += AX_LABEL_Y2_CM
            if not("yticklabel" in gas and gas["yticklabel"] == r"\empty"):
                distr[abs(plt_no)]["borders"][2] += AX_TICKS_Y2_CM
        else:
            distr[abs(plt_no)]["primary"] = [graph_arguments, plots]
            if "ylabel" in gas and gas["ylabel"]:
                distr[abs(plt_no)]["borders"][0] += AX_LABEL_Y1_CM
            if not("yticklabel" in gas and gas["yticklabel"] == r"\empty"):
                distr[abs(plt_no)]["borders"][0] += AX_TICKS_Y1_CM
            if "xlabel" in gas and gas["xlabel"]:
                distr[abs(plt_no)]["borders"][1] += AX_LABEL_X_CM
            if not("xticklabel" in gas and gas["xticklabel"] == r"\empty"):
                distr[abs(plt_no)]["borders"][1] += AX_TICKS_X_CM
            if "title" in gas and gas["title"]:
                distr[abs(plt_no)]["borders"][3] += TITLE_CM 
    limit_grid = {}
    for pk in params.keys():
        if pk == "default": continue
        plt_no = params[pk]["plt_no"]
        if plt_no < 0: continue
        x,y,_,_ = distr[plt_no]["pos"]
        if y not in limit_grid:
            limit_grid[y] = {}
        limit_grid[y][x] = limits[pk].copy()
    macros = []
    def adjust(x1,x2,d1,d2,axis_nm):
        if x1 == float("inf"):
            if f"log basis {axis_nm}" in gas.keys():
                if x1 > 0 and d1 > 0:
                    x1 = 10**(math.log10(d1) - math.log10(d2/d1) * PLOT_AUTOPAD)
                else:
                    x1 = d1
            else:
                x1 = d1 - (d2-d1) * PLOT_AUTOPAD
        if x2 == float("-inf"):
            if "log basis {axis_nm}" in gas.keys():
                if x1 > 0 and d1 > 0:
                    x2 = math.log10(d2) + math.log10(d2/d1) * PLOT_AUTOPAD
                else:
                    x2 = d2
            else:
                x2 = d2 + (d2-d1) * PLOT_AUTOPAD
        return x1,x2
    if xshare == 0:
        x1, x2, d1, d2 = float("inf"), float("-inf"), float("inf"), float("-inf")
        for y in limit_grid.values():
            for x in y.values():
                p1,p2,_,_=x
                if "d" in p1:
                    d1 = min(d1, float(p1[1:]))
                else:
                    x1 = min(x1, float(p1))
                if "d" in p2:
                    d2 = max(d2, float(p2[1:]))
                else:
                    x2 = max(x2, float(p2))
        x1,x2=adjust(x1,x2,d1,d2,"x")
        macros.append(r"\pgfmathsetmacro{\xmin}{" + str(x1) + r"}")
        macros.append(r"\pgfmathsetmacro{\xmax}{" + str(x2) + r"}")
    if xshare == 1:
        for y in limit_grid.keys():
            x1, x2, d1, d2 = float("inf"), float("-inf"), float("inf"), float("-inf")
            for x in limit_grid[y].values():
                p1,p2,_,_=x
                if "d" in p1:
                    d1 = min(d1, float(p1[1:]))
                else:
                    x1 = min(x1, float(p1))
                if "d" in p2:
                    d2 = max(d2, float(p2[1:]))
                else:
                    x2 = max(x2, float(p2))
            x1,x2=adjust(x1,x2,d1,d2,"x")
            macros.append(r"\pgfmathsetmacro{\xmin" + chr(97+y) + r"}{" + str(x1) + r"}")
            macros.append(r"\pgfmathsetmacro{\xmax" + chr(97+y) + r"}{" + str(x2) + r"}")
    if xshare == 2:
        limit_grid_t = {inner_key: {outer_key: inner_dict[inner_key] for outer_key, inner_dict in limit_grid.items() if inner_key in inner_dict}for inner_key in {k for inner_dict in limit_grid.values() for k in inner_dict}}
        for x in limit_grid[0].keys():
            x1, x2, d1, d2 = float("inf"), float("-inf"), float("inf"), float("-inf")
            for y in limit_grid.keys():
                p1,p2,_,_=limit_grid[y][x]
                if "d" in p1:
                    d1 = min(d1, float(p1[1:]))
                else:
                    x1 = min(x1, float(p1))
                if "d" in p2:
                    d2 = max(d2, float(p2[1:]))
                else:
                    x2 = max(x2, float(p2))
            x1,x2=adjust(x1,x2,d1,d2,"x")
            macros.append(r"\pgfmathsetmacro{\xmin" + chr(97+x) + r"}{" + str(x1) + r"}")
            macros.append(r"\pgfmathsetmacro{\xmax" + chr(97+x) + r"}{" + str(x2) + r"}")
    if yshare == 0:
        y1, y2, d1, d2 = float("inf"), float("-inf"), float("inf"), float("-inf")
        for y in limit_grid.values():
            for x in y.values():
                _,_, p1, p2=x
                if "d" in p1:
                    d1 = min(d1, float(p1[1:]))
                else:
                    y1 = min(y1, float(p1))
                if "d" in p2:
                    d2 = max(d2, float(p2[1:]))
                else:
                    y2 = max(y2, float(p2))
        y1,y2=adjust(y1,y2,d1,d2,"y")
        macros.append(r"\pgfmathsetmacro{\ymin}{" + str(y1) + r"}")
        macros.append(r"\pgfmathsetmacro{\ymax}{" + str(y2) + r"}")
    if yshare == 1:
        for y in limit_grid.keys():
            y1, y2, d1, d2 = float("inf"), float("-inf"), float("inf"), float("-inf")
            for x in limit_grid[y].values():
                _,_, p1, p2=x
                if "d" in p1:
                    d1 = min(d1, float(p1[1:]))
                else:
                    y1 = min(y1, float(p1))
                if "d" in p2:
                    d2 = max(d2, float(p2[1:]))
                else:
                    y2 = max(y2, float(p2))
            y1,y2=adjust(y1,y2,d1,d2,"y")
            macros.append(r"\pgfmathsetmacro{\ymin" + chr(97+y) + r"}{" + str(y1) + r"}")
            macros.append(r"\pgfmathsetmacro{\ymax" + chr(97+y) + r"}{" + str(y2) + r"}")
    if yshare == 2:
        limit_grid_t = {inner_key: {outer_key: inner_dict[inner_key] for outer_key, inner_dict in limit_grid.items() if inner_key in inner_dict}for inner_key in {k for inner_dict in limit_grid.values() for k in inner_dict}}
        for x in limit_grid[0].keys():
            y1, y2, d1, d2 = float("inf"), float("-inf"), float("inf"), float("-inf")
            for y in limit_grid.keys():
                _,_, p1, p2=limit_grid[y][x]
                if "d" in p1:
                    d1 = min(d1, float(p1[1:]))
                else:
                    y1 = min(y1, float(p1))
                if "d" in p2:
                    d2 = max(d2, float(p2[1:]))
                else:
                    y2 = max(y2, float(p2))
            y1,y2=adjust(y1,y2,d1,d2,"y")
            macros.append(r"\pgfmathsetmacro{\ymin" + chr(97+x) + r"}{" + str(y1) + r"}")
            macros.append(r"\pgfmathsetmacro{\ymax" + chr(97+x) + r"}{" + str(y2) + r"}")

    tikz_code = r"""\begin{tikzpicture}""" + "\n" + "\n".join(macros)
    if ax_h_def:
        tikz_code += r"""\newcommand{\DrawHline}[4]{
        \pgfplotsextra{
        \pgfkeysgetvalue{/pgfplots/xmin}\xmin
        \pgfkeysgetvalue{/pgfplots/xmax}\xmax
        \pgfmathsetmacro{\xstartval}{\xmin + (#2)*( \xmax - \xmin )}
        \pgfmathsetmacro{\xendval}{\xmin + (#3)*( \xmax - \xmin )}
        }
        \draw[#4] (axis cs:\xstartval,#1) -- (axis cs:\xendval,#1);
        }""" + "\n"
    if ax_v_def:
        tikz_code += r"""\newcommand{\DrawVline}[4]{
        \pgfplotsextra{
        \pgfkeysgetvalue{/pgfplots/ymin}\ymin
        \pgfkeysgetvalue{/pgfplots/ymax}\ymax
        \pgfmathsetmacro{\ystartval}{\ymin + (#2)*( \ymax - \ymin )}
        \pgfmathsetmacro{\yendval}{\ymin + (#3)*( \ymax - \ymin )}
        }
        \draw[#4] (axis cs:#1,\ystartval) -- (axis cs:#1,\yendval);
        }""" + "\n"
    if len(distr.keys()) > 1:
        del(distr[0])
        shifts = {}
        for d in list(sorted(distr.keys())):
            if d <= 0: continue
            x,y,_,_=distr[d]["pos"]
            if (x,y) not in shifts:
                my = distr[y*int(shape[1])+x+1]["borders"]
                shifts[(x,y)] = [my[2], my[3]]
            if y > 0:
                shifts[(x,y)][1] += distr[(y-1)*int(shape[1])+x+1]["borders"][1]
            if x > 0:
                shifts[(x,y)][0] += distr[y*int(shape[1])+x]["borders"][0]
        xspaces = [0 for _ in range(int(shape[1]))]
        yspaces = [0 for _ in range(int(shape[0]))]
        for x in range(0,int(shape[1])):
            for y in range(0,int(shape[0])):
                xspaces[x] = max(xspaces[x], shifts[(x,y)][0])
                yspaces[y] = max(yspaces[y], shifts[(x,y)][1])
    for d in list(sorted(distr.keys())):
        x, y, w, h = distr[d]["pos"]
        w *= dims[0]
        h *= dims[1]
        pos = ""
        if x == 0:
            if y > 0:
                y -= 1
                neigh = f"p{y*int(shape[1])+x+1}"
                pos = r"at={("+neigh+r".south)}, anchor=north, yshift=-" + str(yspaces[y+1]) + r"cm," + "\n"
        else:
            x -= 1
            neigh = f"p{y*int(shape[1])+x+1}"
            pos = r"at={("+neigh+r".east)}, anchor=west, xshift=" + str(xspaces[x+1]) + r"cm," + "\n"
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
            for l in distr[d]["labels"].keys():
                lab, sec = distr[d]["labels"][l]
                if sec and distr[d]["legends"][0]:
                    tikz_code += r"\addlegendimage{/pgfplots/refstyle=lab" + str(l) + r"}\addlegendentry{" + lab + "},\n"
            tikz_code += r"\end{axis}" + "\n"
            if dual:
                tikz_code += r"\begin{axis}["+ "\n"
                tikz_code += f"width={w}cm, height={h}cm,\n"
                tikz_code += r"axis y line*=right, axis x line=none," + "\n"
                tikz_code += r"at={(" + f"p{d}" +r".south west)}, anchor=south west, y label style={at={(1.1,0.5)}, rotate=180},"
                tikz_code += distr[d]["secondary"][0] + "]\n"
                for l in distr[d]["labels"].keys():
                    lab, sec = distr[d]["labels"][l]
                    if not sec and distr[d]["legends"][1]:
                        tikz_code += r"\addlegendimage{/pgfplots/refstyle=lab" + str(l) + r"}\addlegendentry{" + lab + "},\n"
                tikz_code += distr[d]["secondary"][1] + "\n"
                tikz_code += r"\end{axis}" + "\n"
    tikz_code += r"\end{tikzpicture}"
    fn = params["default"]["names"]
    if fn:
        fn = os.path.join(os.path.dirname(path), fn + ".tikz")
    else:
        fn = path.replace(".py", f"{plt_num}.tikz")
    if not DATA_ONLY:
        with open(fn, "w", encoding="utf-8") as f:
            f.write(tikz_code)

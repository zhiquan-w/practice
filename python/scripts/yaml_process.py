from hashlib import sha1
import pathlib
import re
import yaml
import json
import xlsxwriter
import copy

import cfgt_process


class HexInt(int):
    pass


recent_path = pathlib.Path(".")

yaml.add_representer(HexInt, lambda _, data: yaml.ScalarNode("tag:yaml.org,2002:int", hex(data)))


def remove_bracket(string):
    string = string.replace("[", "_").replace("]", "_")
    if string.endswith("_"):
        string = string[:-1]
    return string


def parse_offset(offset):
    if isinstance(offset, list):
        info = offset[0]
        return [0, info // 60, info % 60]
    offset = "0" + str(offset)
    offset = offset.replace(":", ",")
    offset = offset.replace("[", ",")
    offset = offset.replace("]", "")
    offsets = [int(x) for x in str(offset).split(",")]
    if len(offsets) == 1:
        offsets = [0] + offsets + [0]
    elif len(offsets) == 2:
        offsets = [0] + offsets
    return offsets


def get_index(name):
    indexs = re.findall(r"\[(\d+)\]", name)
    if len(indexs) > 0:
        return int(indexs[0])
    else:
        return 1


def new_index(name, index):
    return re.sub(r"\[\d+\]", f"_{index}", name)


def formats(string, var_dict):
    if isinstance(string, str):
        string = re.sub(r"\$(.+?)\$", r"{\1}", string)
        return eval(f'f"{string}"', var_dict)
    return string


def next_power_of_2(x):
    return 1 << (x - 1).bit_length()


def yaml_include_parse(cfg, cfgs):
    if "include" in cfg:
        prefix = cfg["include"].get("prefix", "")
        file, name = cfg["include"]["from"].split(":")
        included = {}
        if file.strip() == "":
            included = yaml_include_parse(cfgs[name], cfgs)
        else:
            new_cfgs = yaml.safe_load((recent_path / file).read_text())
            included = yaml_include_parse(new_cfgs[name], new_cfgs)
            if "include" in included:
                del included["include"]
        for k, v in included.items():
            if prefix == "":
                key = k
            else:
                key = f"{prefix}_{k}"
            cfg[key] = v
    return cfg


def yaml_include(cfgs):
    for v in cfgs.values():
        yaml_include_parse(v, cfgs)
        if "include" in v:
            del v["include"]


def repeat_parse(cfgs, k, v, index):
    filename, key = v["import"].split(":")
    if filename == "":
        reg = cfgs[key]
    else:
        new_cfgs = load_yaml(recent_path / filename)
        reg = new_cfgs[key]
    prefix = formats(v.get("prefix", ""), locals())
    res = {}
    for regname, regcontent in reg.items():
        new_regname = f"{k}_{regname}"
        new_reg = copy.deepcopy(regcontent)  # it's a list of fields
        for field in new_reg:
            if "cname" not in field:
                field["cname"] = field["name"]
            if prefix != "":
                field["name"] = prefix + "_" + field["name"]
            for key in field:
                field[key] = formats(field[key], locals())
            for overwrite in v.get("overwrite", []):
                origin = ""
                if overwrite == "Enabled_by":
                    origin = "1"
                if overwrite in field:
                    origin = formats(field[overwrite], locals())
                field[overwrite] = formats(v["overwrite"][overwrite], locals())
            if "Enabled_by" in field:
                field["Enabled_by"] = field["Enabled_by"].replace("&&1", "")
        res[new_regname] = new_reg
    return res


def yaml_import_parse(cfg, k, v):
    res = []
    for index in range(get_index(k)):
        for newk, newv in repeat_parse(cfg, new_index(k, index), v, index).items():
            res.append((newk, newv))
    return res


def new_append(k, v, index):
    newv = []
    for item in v:
        newitem = item.copy()
        for key in newitem:
            newitem[key] = formats(item[key], locals())
        newv.append(newitem)
    return k, newv


def yaml_import(cfg):
    res = []
    for k, v in cfg.get("regs", {}).items():
        if "import" in v:
            res += yaml_import_parse(cfg, k, v)
        elif get_index(k) != 1:
            for index in range(get_index(k)):
                res.append(new_append(new_index(k, index), v, index))
        else:
            res.append((k, v))
    cfg["regs"] = dict(res)


def permute_field(reg):
    def byte_size(bitwidth):
        return (bitwidth + 7) // 8 * 8

    for field in reg:
        if "[" in str(field.get("offset", "")):
            return
    if len(reg) == 1:
        width = 32
        if "offset" in reg[0]:
            width = reg[0]["offset"]
        reg[0]["offset"] = f"{0}[{width-1}:0]"
        return
    items = []
    total = 0
    for index, field in enumerate(reg):
        items.append([int(field["offset"]), index])
        total += int(field["offset"])
    # assert total <= 32, f"{reg} total bit > 32bit"
    items.sort(reverse=True, key=lambda item: item[0] - item[1])
    for item in items:
        trytos = [next_power_of_2(item[0]), byte_size(item[0])]
        for tryto in trytos:
            if total - item[0] + tryto <= 32:
                item[0] = tryto
                break
    start = 0
    for item in items:
        field = reg[item[1]]
        width = int(field["offset"])
        field["offset"] = f"0[{start+width-1}:{start}]"
        start += width


def make_struct_in(cfgs):
    """
    expand fields from reg
    """
    res = {}
    if "config" in cfgs:
        res["config"] = cfgs["config"]
    for key in cfgs:
        if key != "config":
            res[key] = {}
            for reg, reg_value in cfgs[key].items():
                if "import" in reg_value:
                    res[key][reg] = reg_value
                    continue
                res[key][reg] = reg_value["fields"]
                for k, v in reg_value.items():
                    if k != "fields":
                        res[key][reg][0][k] = v
    return res


def load_yaml(filename):
    regs = yaml.safe_load(open(filename, "r"))
    yaml_include(regs)
    regs = make_struct_in(regs)
    yaml_import(regs)
    for reg in regs["regs"].values():
        permute_field(reg)
    return regs


def make_struct_out(cfgs):
    """
    extract struct/Enabled_by/... out
    """
    res = {}
    res["config"] = cfgs["config"]
    for key in cfgs:
        if key != "config":
            res[key] = {}
            for reg, reg_value in cfgs[key].items():
                if "import" in reg_value:
                    res[key][reg] = reg_value
                    continue
                res[key][reg] = {}
                tmp = []
                new_fields = []
                for field in reg_value:
                    new_field = {}
                    for k, v in field.items():
                        if k not in ["name", "cname", "offset", "reset_val", "type", "desc"]:
                            tmp.append((k, v))
                        else:
                            if k == "reset_val":
                                v = HexInt(v)
                            new_field[k] = v
                    new_fields.append(new_field)
                tmp.sort(reverse=True)
                res[key][reg].update(dict(tmp))
                res[key][reg]["fields"] = new_fields
    return res


def yaml2json(yaml_file):
    regs = load_yaml(yaml_file)
    res = {}
    res["config"] = regs["config"].copy()
    res["config"]["excel_sha1"] = sha1(open(yaml_file, "rb").read()).hexdigest()
    base_offset = res["config"].get("regs_offset_base", 0)
    res["reglist"] = {}
    base = {
        "name": "",
        "reset_val": 0,
        "desc": "",
        "cname": "",
        "Enabled_by": "",
        "struct": "",
        "Data_type": "",
        "True_struct_name": "",
        "Cmodel_bit_width": "",
        "Cmodel_to_reg_map": "",
        "Appended_to_cfgt": "",
    }
    i = 0
    append_i = len(regs["regs"])
    for key, value in regs["regs"].items():
        append = value[0].get("append", False)
        if append:
            offset = append_i * 4
            append_i += 1
        else:
            offset = i * 4
            i += 1
        reg = {
            "is_mcode_reg": True,
            "offset": base_offset + offset,
            "reg_name": key,
            "field": {},
            "append": append,
        }
        for field in value:
            if "type" in field:
                if field["type"] not in ["M_W1C", "M_WO"]:
                    reg["is_mcode_reg"] = False
                    break
        for field in value:
            info = base.copy()
            info.update(field)
            if info["cname"] == "":
                info["cname"] = info["name"]
            info["name"] = remove_bracket(info["name"])
            renames = ["field_desc:desc", "Cmodel Name:cname", "Struct:struct", "field_name:name"]
            for rename in renames:
                new, old = rename.split(":")
                info[new] = info[old]
                del info[old]
            _, msb, lsb = parse_offset(info["offset"])
            info["msb"] = msb
            info["lsb"] = lsb
            reg["field"][field["name"]] = info
        res["reglist"][f"{offset}"] = reg
    return res


def yaml2xlsx(yaml_file, xlsx_file):
    regs = load_yaml(yaml_file)
    config = {
        "addr_width": 13,
        "data_width": 32,
        "if": "apb",
        "mcode_if_type": "sram_wr",
        "mcode_addr_width": 14,
        "mcode_data_width": 32,
        "clock": "clk",
        "reset": "rst_n",
        "use_reg_name": False,
        "use_rd": True,
        "set_clr_method": None,
        "base_addr": 0,
        "regs_offset_base": 0,
    }
    config.update(regs["config"])
    base_offset = config["regs_offset_base"]
    workbook = xlsxwriter.Workbook(xlsx_file)
    cf = workbook.add_worksheet("config")
    names = [
        "Module Name:modu_name",
        "Address Width:addr_width",
        "Data Width:data_width",
        "Interface:if",
        "Mcode Interface:mcode_if_type",
        "Mcode Address Width:mcode_addr_width",
        "Mcode Data Width:mcode_data_width",
        "Clock:clock",
        "Reset:reset",
        "Use reg and field name:use_reg_name",
        "Use RD macro:use_rd",
        "Set/Clear Method:set_clr_method",
        "Use array style",
        "Set Base Offset",
        "Clear Base Offset",
        "Version:version",
        "Instance Name",
        "Base Address:base_addr",
    ]
    for i, value in enumerate(names):
        name = value.split(":")
        cf.write(i, 0, name[0])
        if len(name) > 1:
            val = config[name[1]]
            if val is None:
                val = "None"
            elif isinstance(val, bool):
                if val:
                    val = "Yes"
                else:
                    val = "No"
            cf.write(i, 1, val)
    cf.set_column(0, 2, 25)
    rg = workbook.add_worksheet("reglist")
    head = [
        "Reg Name",
        "Reg Description",
        "Field Name",
        "Bits",
        "Type",
        "Reset Value",
        "Set",
        "Clear",
        "Field Description",
        "Cmodel Name",
        "Acc",
        "Shad",
        "FA_2",
        "FA_3",
        "Enabled_by",
        "Struct",
        "Data_type",
        "True_struct_name",
        "Cmodel_bit_width",
        "Cmodel_to_reg_map",
        "Appended_to_cfgt",
    ]
    if base_offset != 0:
        head = ["offset"] + head
    for i, h in enumerate(head):
        rg.write(0, i, h)

    def gen_bits(offset):
        _, msb, lsb = parse_offset(offset)
        if msb == lsb:
            return f"[{msb}]"
        return f"[{msb}:{lsb}]"

    def gen_reset_val(val, offset):
        _, msb, lsb = parse_offset(offset)
        length = msb - lsb + 1
        return f"{length}'h{val:x}"

    rows = []
    new_regs = []
    for reg, value in regs["regs"].items():
        if value[0].get("append", False):
            continue
        value[0]["reg_name"] = reg
        new_regs += value
    offset = 0
    for reg in new_regs:
        base = {
            "reg_name": "",
            "name": "",
            "type": "M_WO",
            "reset_val": 0,
            "desc": "",
            "cname": "",
            "Enabled_by": "",
            "struct": "",
            "Data_type": "",
            "True_struct_name": "",
            "Cmodel_bit_width": "",
            "Cmodel_to_reg_map": "",
            "Appended_to_cfgt": "",
        }
        base.update(reg)
        base["name"] = remove_bracket(base["name"])
        row = []
        row.append((0, base["reg_name"]))
        if base["reg_name"] != "":
            row.append((1, f"offset: {offset}"))
            offset += 4
        row.append((2, base["name"]))
        row.append((3, gen_bits(base["offset"])))
        row.append((4, base["type"]))
        row.append((5, gen_reset_val(base["reset_val"], base["offset"])))
        row.append((8, base["desc"]))
        row.append((9, base["cname"]))
        row.append((14, base["Enabled_by"]))
        row.append((15, base["struct"]))
        row.append((16, base["Data_type"]))
        row.append((17, base["True_struct_name"]))
        row.append((18, base["Cmodel_bit_width"]))
        row.append((19, base["Cmodel_to_reg_map"]))
        row.append((20, base["Appended_to_cfgt"]))
        rows.append(row)
    width = {}
    for i in range(32):
        width[i] = 4
    for i, row in enumerate(rows):
        row_index = i + 1
        for col_index, val in row:
            if base_offset != 0:
                if col_index == 1:
                    rg.write(row_index, 0, hex(base_offset + int(val[8:])))
                col_index += 1
            val_len = len(str(val))
            if val_len > width.get(col_index, 0):
                width[col_index] = val_len
            rg.write(row_index, col_index, val)
    for k, v in width.items():
        rg.set_column(k, k, min(int(v * 1.5), 20))
    workbook.close()


def json2yaml(jsonfile, yamlfile):
    data = json.loads(open(jsonfile, "r").read())
    yaml_regs = {}
    yaml_regs["config"] = {"modu_name": data["config"]["modu_name"], "version": data["config"]["version"]}
    res = {}
    regs = data["reglist"]  # type:dict
    for index, reg in regs.items():
        res[reg["reg_name"]] = []
        for key, field in reg["field"].items():
            if field["field_desc"] == "Reserved":
                continue
            delkeys = [
                "field_name_without_index",
                "has_clr",
                "has_reset",
                "has_set",
                "is_rsv",
                "sec",
                "field_desc_with_misc",
            ]
            info = field.copy()
            for k in field:
                if info[k] == "" or k in delkeys:
                    del info[k]
            if info["reset_val"] == 0:
                del info["reset_val"]
            else:
                info["reset_val"] = HexInt(info["reset_val"])
            lsb = info["lsb"]
            msb = info["msb"]
            index = int(index)
            info["offset"] = f"{index}[{msb}:{lsb}]"
            if info["type"] == "M_WO":
                del info["type"]
            del info["lsb"]
            del info["msb"]
            assert key == info["field_name"]
            renames = ["field_desc:desc", "Cmodel Name:cname", "Struct:struct", "field_name:name"]
            for rename in renames:
                old, new = rename.split(":")
                if old in info:
                    info[new] = info[old]
                    del info[old]
            if "cname" in info and info["cname"] == info["name"]:
                del info["cname"]
            # del info["field_name"]
            # info["reg_name"] = reg["reg_name"]
            # res[key] = info
            info = dict(sorted(info.items(), key=lambda item: (item[0] != "name", item[0])))
            for key, value in info.items():
                if isinstance(value, str):
                    info[key] = value.strip()
            res[reg["reg_name"]].append(info)
    res = dict(sorted(res.items(), key=lambda item: parse_offset(item[1][0]["offset"])))
    yaml_regs["regs"] = res
    yaml_regs = make_struct_out(yaml_regs)
    yaml.dump(yaml_regs, open(yamlfile, "w"), sort_keys=False)


def gen_cfg(yamlfile, driver, sv, mcode, output):
    global recent_path
    recent_path = pathlib.Path(yamlfile).parent
    data = yaml2json(yamlfile)
    excel_sha1 = data["config"]["excel_sha1"]
    module_name = data["config"]["modu_name"].split("_")[1]
    regs = cfgt_process.RegTree(data, module_name)
    cfg_t = regs.gen_cfg_t()
    if driver:
        cfgt_process.cfg_t_print(cfg_t, excel_sha1, module_name, output)
    if sv:
        cfgt_process.cfg_sv_print(cfg_t, excel_sha1, module_name, output)
    if mcode:
        cfgt_process.mcode_print(regs, excel_sha1, module_name, topkey=cfg_t[-1]["key"], output_dir=output)
        cfgt_process.mcode_disassemble_print(regs, excel_sha1, module_name, cfg_t[-1]["key"], output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="json_file")
    parser.add_argument("--yaml", help="yaml_file")
    parser.add_argument("--excel", help="excel_file")
    parser.add_argument("--mcode", help="generate mcode", action="store_true", default=False)
    parser.add_argument("--sv", help="generate mcode", action="store_true", default=False)
    parser.add_argument("--driver", help="generate mcode", action="store_true", default=False)
    parser.add_argument("--output", help="output dir", default=".")
    parser.add_argument("--all", help="generate all", action="store_true", default=False)
    args = parser.parse_args()
    if args.yaml:
        recent_path = pathlib.Path(args.yaml).parent
    if args.all:
        for filename in ["driver/conv.yaml", "driver/cv.yaml", "driver/teng.yaml", "driver/mau.yaml"]:
            gen_cfg(filename, True, True, True, "driver")
    elif args.yaml and args.json:
        json2yaml(args.json, args.yaml)
    elif args.yaml and args.excel:
        yaml2xlsx(args.yaml, args.excel)
    elif args.yaml:
        gen_cfg(args.yaml, args.driver, args.sv, args.mcode, args.output)

import pathlib
import shutil
import re
import json
import random
import string
import typing

import dataclasses
import collections


def remove_list(string):
    return re.sub(r"\[\d+\]", "", string)


def get_index(name):
    indexs = re.findall(r"\[(\d+)\]", name)
    if len(indexs) > 0:
        return int(indexs[0])
    return -1


@dataclasses.dataclass
class McodeCaseInfo(object):
    index: int
    info: str


class Table(dict):
    def __init__(self, other: dict = None):
        if other is not None:
            for k, v in other.items():
                self[k] = v

    def __getitem__(self, name):
        if name not in self:
            self[name] = Table()
        return super().__getitem__(name)

    def __getattr__(self, name):
        return self[name] if name in self else None

    def __setattr__(self, name, value):
        if value is not None:
            self[name] = value
        elif name in self:
            del self[name]

    def __delattr__(self, name):
        self.__setattr__(name, None)


class ItemInfo(Table):
    utypes = [f"AX_NPU_U{i+1}" for i in range(64)]
    itypes = [f"AX_NPU_I{i+1}" for i in range(64)]

    def __init__(self, info=None):
        if type(info) == ItemInfo:
            super().__init__(info)
        elif info is not None:
            self.name = info["Cmodel Name"].strip()
            self.data_type = info["Data_type"] or "uint"
            self.range = [(info["lsb"], info["msb"])]
            self.length = info["msb"] - info["lsb"] + 1
            if info.get("Cmodel_bit_width", "") != "":
                self.longlength = int(info["Cmodel_bit_width"])
            else:
                self.longlength = self.length
            self.reset_val = info["reset_val"]
            self.enabled_by = info["Enabled_by"]
            self.struct = info["Struct"]
            # self.true_name = info["True_struct_name"]
            self.address = [int(info["index"])]
            self.index = get_index(self.name)
            self.appended = [x.strip() for x in info.get("Appended_to_cfgt", "").split(",") if x.strip() != ""]
            self.comment = [e for e in info.get("field_desc", "").split("\n") if e.strip() != ""]
            if self.name == "":
                self.name = info["field_name"].strip()
            assert self.name != "", f"reg {self.address} no Cmodel Name"

    def __eq__(self, other):
        return self.name[:-1] == other.name[:-1] and self.name[-1] in "hl" and other.name[-1] in "hl"

    def __add__(self, other):
        res = ItemInfo(self)
        res.data_type = self.data_type
        res.index = self.index
        if type(other) == int:
            res.name = self.name
            res.length = self.length
            res.range = self.range
            res.address = self.address
            if res.index >= 0:
                res.index += other
            return res
        res.name = self.name[:-2]
        res.length = self.length + other.length
        res.longlength = self.longlength + other.longlength
        res.range = self.range + other.range
        res.address = self.address + other.address
        assert self.data_type == other.data_type
        return res

    def get_name(self):
        if self.index < 0:
            return self.name
        else:
            return re.sub(r"\[\d+\]", f"[{self.index}]", self.name)

    def __str__(self):
        types = self.utypes
        comment = []
        for i in range(len(self.range)):
            comment.append(f"reg [{self.range[i][1]}:{self.range[i][0]}]")
        if self.data_type != "uint":
            types = self.itypes
        if len(self.comment) > 0:
            return (
                f"    {types[self.longlength-1]}".ljust(28)
                + f" {self.get_name()};".ljust(32)
                + f" // "
                + "||".join(self.comment)
            )
        else:
            return f"    {types[self.longlength-1]}".ljust(28) + f" {self.get_name()};"

    def sv_str(self):
        return f"rand bit[{self.longlength}-1:0] {self.get_name()};"

    def mcode_str(self, name, hl_map):
        mask = hex(2 ** self.length - 1) + "u"
        left = self.range[0][0]
        self_name = self.get_full_name()
        if self.name.endswith("_l"):
            return f"{name} |= ({mask} & {self_name}) << {left};"
        elif self.name.endswith("_h"):
            right = hl_map[self.name[:-2]]
            return f"{name} |= ({mask} & ({self_name} >> {right})) << {left};"
        return f"{name} |= ({mask} & {self_name}) << {left};"

    def get_full_name(self):
        self_name = f"{self.struct}.{self.get_name()}"
        self_name = self_name.replace(".", "->", 1)
        if self_name.endswith("_l") or self_name.endswith("_h"):
            self_name = self_name[:-2]
        return self_name

    def mcode_disassemble(self, name, hl_map):
        mask = hex(2 ** self.length - 1) + "ul"
        self_name = self.get_full_name()
        res = []
        left = self.range[0][0]
        if self.name.endswith("_l"):
            res.append(f"{self_name} &= ~{mask};")
            res.append(f"{self_name} |= ({mask} & ({name} >> {left}));")
            total_bits = None
        elif self.name.endswith("_h"):
            right = hl_map[self.name[:-2]]
            res.append(f"{self_name} &= ~({mask}<<{right});")
            res.append(f"{self_name} |= ({mask} & ({name} >> {left})) << {right};")
            total_bits = self.length + right
        else:
            res.append(f"{self_name} = {mask} & ({name} >> {left});")
            total_bits = self.length
        if self.data_type != "uint" and total_bits is not None:
            # Sign extend.
            # TODO: Improve this code.
            if total_bits > 32:
                cfg_type = "int64_t"
                shift = 64 - total_bits
            else:
                cfg_type = "int32_t"
                shift = 32 - total_bits
            res.append(f"{self_name} = {cfg_type}({self_name}) << {shift} >> {shift};")
        res = ["  " + r for r in res]
        return "\n".join(res)

    def cfg_str(self):
        return f"{self.struct}.{self.get_name()}"


class StructInfo(Table):
    def __init__(self, k, name="", prefix=""):
        no_list_k = remove_list(k)
        if no_list_k.startswith(prefix):
            self.struct = "_".join([no_list_k, "t"])
        else:
            self.struct = "_".join([prefix, no_list_k, "t"])
        self.index = get_index(k)
        if name != "":
            self.index -= 128
        self.name = name if name != "" else no_list_k

    def __eq__(self, other):
        return self.name == other.name

    def __add__(self, other):
        if self.index >= 0:
            self.index += other
        return self

    def __str__(self):
        index = f"[{self.index}]" if self.index > 0 else ""
        return f"    {self.struct}".ljust(28) + f" {self.name}{index};"

    def sv_str(self):
        index = f"[{self.index}]" if self.index > 0 else ""
        return f"rand {self.struct} {self.name}{index}"


class EnableInfo(Table):
    def __init__(self, reg, true_struct_name_map, index):
        def parse(struct, struct_name_map):
            res = []
            for split in struct.split("/"):
                res.append(".".join([struct_name_map.get(s, s) for s in split.split(".")]))
            if index < len(res):
                return res[index]
            else:
                return res[0]

        self.reg_name = reg["reg_name"]
        self.offset = reg["offset"]
        self.fields: typing.List[ItemInfo] = []
        self.index = index
        for _, v in reg["field"].items():
            if "Struct" in v:
                tmp = v.copy()
                tmp["Struct"] = parse(v["Struct"], true_struct_name_map)
                self.struct = tmp["Struct"]
                self.fields.append(ItemInfo(tmp))

    def get_hl_map(self):
        res = {}
        for field in self.fields:
            if field.name.endswith("_l"):
                res[field.name[:-2]] = field.length
        return res

    def set_hl_map(self, hl_map):
        self._hl_map = hl_map
        return self

    def __str__(self):
        res = []
        res.append(f"// {self.reg_name}")
        res.append(f"offset = {self.offset};")
        res.append(f"reg = 0;")
        for field in self.fields:
            res.append(field.mcode_str("reg", self._hl_map))
        res.append("mcode_push(mcode, reg, ((offset / 4) << 20) | MCODE_LOADi);")
        return "\n".join(res)

    def mcode_disassemble(self):
        res = []
        res.append(f"  // {self.reg_name}")
        for field in self.fields:
            res.append(field.mcode_disassemble("cmd_h", self._hl_map))
        return McodeCaseInfo(index=self.offset // 4, info="\n".join(res))


class MEMRegInfo(Table):
    def __init__(self, reg, true_struct_name_map):
        def parse(struct, struct_name_map):
            res = []
            for split in struct.split("/"):
                res.append(".".join([struct_name_map.get(s, s) for s in split.split(".")]))
            return res[0]

        self.reg_name = reg["mem_name"]
        self.start = reg["start"]
        self.length = reg["depth"]
        self.data_width = reg["data_width"]
        self.struct = parse(reg["Struct"], true_struct_name_map)

    def get_hl_map(self):
        return {}

    def set_hl_map(self, hl_map):
        return self

    def __str__(self):
        mask = hex(2 ** self.data_width - 1) + "u"
        res = []
        res.append(f"for (int i = 0; i < {self.length}; ++i) {{")
        res.append(f"    offset = {self.start} + i * 4;")
        res.append(f"    reg = {self.struct}.{self.reg_name}[i] & {mask};")
        res.append(f"    mcode_push(mcode, reg, ((offset / 4) << 20) | MCODE_LOADi);")
        res.append(f"}}")
        return "\n".join(res)


class RegTree:
    def __init__(self, data, prefix):
        self._root = Table()
        self._enables = {}
        self._mcode_disassemble = []
        self._names = {}
        self._true_struct_name_map = {}
        self._prefix = prefix
        reglist = data["reglist"]

        def prepare_reglist(reglist):
            new_list = {}
            for offset in reglist:
                cur_reg = reglist[offset]
                if not (cur_reg["is_mcode_reg"] or cur_reg.get("append", False)):
                    continue
                for field in cur_reg["field"].values():
                    if field.get("Enabled_by", "") != "":
                        cur_reg["Enabled_by"] = field["Enabled_by"]
                        break
                else:
                    cur_reg["Enabled_by"] = "1"
                for field in cur_reg["field"].values():
                    if field.get("Struct", "").strip() != "":
                        cur_reg["Struct"] = field["Struct"]
                        break
                else:
                    continue
                for field_name in list(cur_reg["field"]):
                    value = cur_reg["field"][field_name]
                    value["index"] = offset
                    if "Struct" not in value:
                        del cur_reg["field"][field_name]
                    value["Struct"] = cur_reg["Struct"].strip()
                new_list[offset] = cur_reg
            return new_list

        for offset in prepare_reglist(reglist):
            cur_reg = reglist[offset]
            for _, v in cur_reg["field"].items():
                if v["True_struct_name"] != "":
                    self._true_struct_name_map[v["Struct"].split(".")[-1]] = v["True_struct_name"]
                self[v["Struct"]] = ItemInfo(v)
                self._names[v["field_name"]] = ItemInfo(v)

        hl_map = {}

        for offset in prepare_reglist(reglist):
            cur_reg = reglist[offset]
            if cur_reg["append"]:
                continue
            flag = False
            for field_name in list(cur_reg["field"]):
                value = cur_reg["field"][field_name]
                if value.get("Cmodel_to_reg_map", "").strip() != "":
                    flag = True
            if flag:
                continue
            self._enables[cur_reg["Enabled_by"]] = self._enables.get(cur_reg["Enabled_by"], [])
            for i in range(len(cur_reg["Struct"].split("/"))):
                self._enables[cur_reg["Enabled_by"]].append(EnableInfo(cur_reg, self._true_struct_name_map, i))
                enable_info = EnableInfo(cur_reg, self._true_struct_name_map, i)
                hl_map.update(enable_info.get_hl_map())
                enable_info.set_hl_map(hl_map)
                self._mcode_disassemble.append(enable_info)

    def __setitem__(self, keyring, value):
        for key in keyring.split("/"):
            last = self._root
            for k in key.strip().split("."):
                last = last[k]
            length = len(last)
            last[f"field{length}"] = value

    def gen_cfg_t(self):
        for key, value in self._root.items():
            res = self.gen_cfg_t_v2(value, key)
            return res

    def gen_cfg_t_v2(self, d: dict, key: str):
        def struct_merge(cfg_t: list):
            """
            merge
                cfg_t cfg[0];
                cfg_t cfg[1];
            to
                cfg_t cfg[2];
            """
            if len(cfg_t) == 0:
                return cfg_t
            res = [cfg_t[0] + 1]
            for item in cfg_t[1:]:
                if item == res[-1]:
                    res[-1] = res[-1] + 1
                else:
                    res.append(item + 1)
            return res

        def item_merge(cfg_t: list, index_add=1):
            """
            merge
                AX_NPU_U1 cfg_l;
                AX_NPU_U1 cfg_h;
            to
                AX_NPU_U2 cfg;
            """
            if len(cfg_t) == 0:
                return cfg_t
            res = [cfg_t[0] + index_add]
            for item in cfg_t[1:]:
                if item == res[-1]:
                    res[-1] = res[-1] + item
                elif remove_list(item.name) == remove_list(res[-1].name):
                    res[-1] = res[-1] + 1
                else:
                    res.append(item + index_add)
            return res

        cfg_t = []
        uint_cfg_t = []
        struct_cfg_t = []
        for k, v in d.items():
            if "range" in v:
                uint_cfg_t.append(v)
            else:
                cfg_t = self.gen_cfg_t_v2(v, remove_list(k)) + cfg_t
                name = self._true_struct_name_map.get(k, "")
                struct_cfg_t.append(StructInfo(k, name, self._prefix))

        uint_cfg_t = item_merge(sorted(uint_cfg_t, key=lambda x: x.name))
        uint_cfg_t = item_merge(uint_cfg_t, 0)
        struct_cfg_t = struct_merge(sorted(struct_cfg_t, key=lambda x: (remove_list(x.name), x.index)))
        uint_cfg_t = sorted(uint_cfg_t, key=lambda x: (x.address[0], x.range))
        cur = {}
        cur["key"] = key
        cur["uint_cfg"] = uint_cfg_t
        cur["struct_cfg"] = struct_cfg_t
        cfg_t.append(cur)
        return cfg_t

    def gen_mcode_disassemble(self):
        res = []
        for item in self._mcode_disassemble:
            res.append(item.mcode_disassemble())
        return res

    def gen_mcode(self, split_list=[]):
        def parse(struct, struct_name_map):
            res = []
            for split in struct.split("/"):
                res.append(".".join([struct_name_map.get(s, s) for s in split.split(".")]))
            if index < len(res):
                return res[index]
            else:
                return res[0]

        res = [[] for _ in range(len(split_list) + 1)]

        def get_reg_index(reg):
            for i, item in enumerate(split_list):
                if item in reg.struct:
                    return item, i
            return "", len(split_list)

        def gen_condition(enable_cond, match):
            enable_cond = str(enable_cond).replace("&&", "&").replace("&", "&&")

            condition = []
            for cond in enable_cond.split("&&"):
                if cond == "1" or cond == "":
                    condition.append("1")
                    continue
                if cond == "0.0":
                    condition.append("0")
                    continue
                condition.append(cond.strip())
            enable_cond = " && ".join(condition)

            for cond in re.findall(r"\w+(?:\[\d+\])?", enable_cond):
                if cond == "0" or cond == "1":
                    continue
                real_cond = remove_list(cond)
                index = -1
                if real_cond.strip() not in self._names:
                    condition.append(cond)
                    continue
                item = self._names[real_cond.strip()]
                the_struct = parse(item.struct, self._true_struct_name_map)
                if "/" in item.struct:
                    for st in item.struct.split("/"):
                        if match in st:
                            the_struct = st
                            break
                item_name = f"{the_struct}.{item.get_name()}"
                item_name = item_name.replace(".", "->", 1)
                if real_cond != cond:
                    index = int(cond[len(real_cond) + 1 : -1])
                    local_name = f"(({item_name} >> {index}) & 0x1)"
                else:
                    mask = hex(2 ** item.length - 1)
                    local_name = f"({item_name} & {mask})"
                enable_cond = enable_cond.replace(cond, local_name)

            res_head = []
            res_head.append("")
            res_head.append(f"if({enable_cond}) {{")
            return res_head

        for enable_cond in self._enables:
            res_with_head = []
            hl_map = {}
            for reg in self._enables[enable_cond]:
                hl_map.update(reg.get_hl_map())
            for reg in self._enables[enable_cond]:
                match, index = get_reg_index(reg)
                if index not in res_with_head:
                    res_with_head.append(index)
                    res[index] += gen_condition(enable_cond, match)
                res[index].append("")
                reg.set_hl_map(hl_map)
                for line in str(reg).split("\n"):
                    res[index].append("    " + line)
                res[index].append("")
            for index in res_with_head:
                res[index].append("}")
                res[index].append("")
        return ["\n".join(r) for r in res]


def cfg_t_print(cfg_t, excel_sha1, module_name, output_dir="."):
    output_dir = pathlib.Path(output_dir)
    filename = f"{module_name}_cfg.h"
    structs = {}
    res = []
    res.append('#include "define.h"')
    res.append("")
    guard = filename.replace(".", "_").upper()
    res.append(f"#ifndef {guard}")
    res.append(f"#define {guard}")
    res.append(f'#include "{module_name}.cfg"')
    res.append(f"#endif // {guard}")
    with open(output_dir / filename, "w") as f:
        f.write("\n".join(res))
    res = []
    for item in cfg_t:
        struct = []
        if item["key"] not in structs:
            structs[item["key"]] = []
        struct.append("typedef struct {")
        for cfg in item["uint_cfg"]:
            struct.append(str(cfg))
            if cfg.appended is not None:
                for appended in cfg.appended[::-1]:
                    struct.insert(1, f"    AX_NPU_U32               {appended};")
        for cfg in item["struct_cfg"]:
            struct.append(str(cfg))
        if item == cfg_t[-1] or item["key"].startswith(module_name):
            struct.append(f"}} {item['key']}_t;")
        else:
            struct.append(f"}} {module_name}_{item['key']}_t;")
        struct.append("")
        structs[item["key"]].append(struct)
    for key in structs:
        res += max(structs[key], key=len)
    with open(output_dir / f"{module_name}.cfg", "w") as f:
        f.write("\n".join(res))


def mcode_disassemble_print(regs: RegTree, excel_sha1, module_name, topkey, output_dir="."):
    output_dir = pathlib.Path(output_dir)
    infos = regs.gen_mcode_disassemble()
    res = []
    res.append(f"// Automatically generated, DO NOT MODIFY!")
    res.append(f"// {excel_sha1}")
    res.append(f"#include <assert.h>")
    res.append(f'#include "{module_name}_disassemble.h"')
    res.append(f"void {module_name}_mcode_disassemble({topkey}_t *{topkey}, uint32_t cmd_h, uint32_t cmd_l) {{")
    res.append("  uint32_t offset = cmd_l >> 20;")
    res.append("  assert((cmd_l & 0xFFFFF) == MCODE_LOADi);")
    res.append("  switch (offset) {")
    info_groups = collections.defaultdict(list)
    for info in infos:
        info_groups[info.index].append(info)
    for index, sub_infos in info_groups.items():
        res.append(f"  case {index}:")
        for info in sub_infos:
            tab_info = ["  " + i for i in info.info.split("\n")]
            res += tab_info
        res.append("    break;")
    res.append("  }")
    res.append("}")
    (output_dir / f"{module_name}_disassemble.cpp").write_text("\n".join(res))
    (output_dir / f"{module_name}_disassemble.h").write_text(
        f"""#pragma once
#include <stdint.h>
#include "{module_name}_cfg.h"

#ifdef __cplusplus
extern "C" {{
#endif
void {module_name}_mcode_disassemble({topkey}_t *{topkey}, uint32_t cmd_h, uint32_t cmd_l);
#ifdef __cplusplus
}}
#endif
"""
    )


def cfg_sv_print(cfg_t, excel_sha1, module_name, output_dir="."):
    structs = {}

    dirs = pathlib.Path(output_dir) / f"{module_name}_sv"
    if dirs.exists():
        shutil.rmtree(dirs)
    dirs.mkdir(parents=True)
    with open(dirs / "sha1.txt", "w") as f:
        f.write(f"{excel_sha1}")
    for item in cfg_t:
        struct = []
        if item["key"] not in structs:
            structs[item["key"]] = []
        for cfg in item["uint_cfg"]:
            struct.append(cfg.sv_str())
            if cfg.appended is not None:
                for appended in cfg.appended[::-1]:
                    struct.insert(1, f"rand bit[32-1:0] {appended};")
        # for cfg in item["struct_cfg"]:
        #     struct.append(cfg.sv_str())
        structs[item["key"]].append(struct)
    for key in structs:
        with open(dirs / f"{key}.sv", "w") as f:
            res = max(structs[key], key=len)
            f.write("\n".join(res))


def mcode_print(regs: RegTree, excel_sha1, module_name, topkey, output_dir="."):
    output_dir = pathlib.Path(output_dir)
    split_list = ["idle_mask_cfg", "start_cfg", "idle_pattern_cfg"]
    split_len = len(split_list)
    if module_name == "conv":
        split_list += ["bk_dma_cfg", "weight_dma_cfg"]
    infos = regs.gen_mcode(split_list)
    # hack here
    split_list = [module_name + "_" + v for v in split_list[:split_len]] + split_list[split_len:]
    res = []
    res.append(f'#include "{module_name}_cfg.h"')
    res.append(f'#include "mcode.h"')
    res.append("")
    res.append(f"void {module_name}_mcode(const {topkey}_t* {topkey}, mcode_t* mcode){{")
    res.append("    uint32_t offset;")
    res.append("    uint32_t reg;")
    res += [("    " + line).rstrip() for line in infos[-1].split("\n")]
    res.append("}")
    for index in range(len(split_list)):
        res.append("")
        res.append(f"void {split_list[index]}_mcode(const {topkey}_t* {topkey}, mcode_t* mcode){{")
        res.append("    uint32_t offset;")
        res.append("    uint32_t reg;")
        res += [("    " + line).rstrip() for line in infos[index].split("\n")]
        res.append("}")
    with open(output_dir / f"{module_name}.c", "w") as f:
        f.write("\n".join(res))
    with open(output_dir / f"{module_name}.h", "w") as f:
        f.write(f'#include "{module_name}_cfg.h"\n')
        f.write(f'#include "mcode.h"\n')
        f.write(f"#ifndef {module_name.upper()}_MCODE\n")
        f.write(f"#define {module_name.upper()}_MCODE\n")
        f.write("#ifdef __cplusplus\n")
        f.write('extern "C" {\n')
        f.write("#endif\n")
        f.write(f"void {module_name}_mcode(const {topkey}_t* {topkey}, mcode_t* mcode);\n")
        for l in split_list:
            f.write(f"void {l}_mcode(const {topkey}_t* {topkey}, mcode_t* mcode);\n")
        f.write("#ifdef __cplusplus\n")
        f.write("}\n")
        f.write("#endif\n")
        f.write(f"#endif // {module_name.upper()}_MCODE\n")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--excel", help="Excel file path", required=True)
    parser.add_argument("--sv", help="whether ouput sv", action="store_true", default=False)
    parser.add_argument("--mcode", help="whether ouput mcode", action="store_true", default=False)
    parser.add_argument("--output", help="output dir", default=".")
    args = parser.parse_args()
    data = json.loads(open(args.excel, "r").read())
    excel_sha1 = data["config"]["excel_sha1"]
    module_name = data["config"]["modu_name"].split("_")[1]
    regs = RegTree(data, module_name)
    cfg_t = regs.gen_cfg_t()
    cfg_t_print(cfg_t, excel_sha1, module_name, args.output)
    mcode_disassemble_print(regs, excel_sha1, module_name, cfg_t[-1]["key"], args.output)
    if args.sv:
        cfg_sv_print(cfg_t, excel_sha1, module_name, args.output)
    if args.mcode:
        mcode_print(regs, excel_sha1, module_name, topkey=cfg_t[-1]["key"], output_dir=args.output)
    with open("{module_name}.sha1", "w") as f:
        f.write(f"{excel_sha1}")


if __name__ == "__main__":
    main()

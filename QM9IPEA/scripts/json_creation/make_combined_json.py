# Created a combined json from cleaned results dir.
import json
import os
import sys

charges = [0, 1, -1]

charge_string = {0: "0", 1: "1", -1: "m1"}

atom_mol_method_dict = {
    "DFRHF": "DFHF",
    "DFRHF+CABS": "DFHF+CABS",
    "PNO-LRMP2-F12": "PNO-LMP2-F12",
    "PNO-UCCSD-F12B": "PNO-LCCSD-F12B",
    "PNO-UCCSD(T)-F12B": "PNO-LCCSD(T)-F12B",
    "PNO-UCCSD(T*)-F12B": "PNO-LCCSD(T*)-F12B",
}

MANDATORY_PROGRAM_FIELDS = ["INT", "FILE", "RESTART"]


def xyz_subdir_to_qm9_id(subdir):
    base = os.path.basename(subdir)
    bspl = base.split("_")
    return int(bspl[1])


def filename_root(subdir, charge=0):
    base = os.path.basename(subdir)
    return subdir + "/" + base + "_charge_" + charge_string[charge] + "."


def xyz_subdir_is_valid(subdir):
    if not os.path.isdir(subdir):
        return False
    if (len(subdir) < 4) or (subdir[-4:] != "_xyz"):
        return False
    return True


def valid_xyz_subdirs(root_dir):
    output = []
    for subdir in os.listdir(root_dir):
        true_subdir = root_dir + "/" + subdir
        if xyz_subdir_is_valid(true_subdir):
            output.append(true_subdir)
    return sorted(output)


def get_file_lines(filename):
    return open(filename, "r").readlines()


def calculation_converged(file_lines):
    final_line = file_lines[-1]
    final_line_spl = final_line.split()
    return final_line_spl == ["Molpro", "calculation", "terminated"]


def get_energies(lines):
    final_result_lines = False
    output = {}
    for line in lines:
        lspl = line.split()
        if len(lspl) == 2 and lspl[0] == "METHOD" and lspl[1] == "ETOT":
            final_result_lines = True
            continue
        if not final_result_lines:
            continue
        if len(lspl) == 0:
            return output
        output[lspl[0]] = float(lspl[1])
    return None


def get_CPU_times(lines):
    final_programs_line = None
    final_CPU_line = None
    for line in lines:
        lspl = line.split()
        if len(lspl) > 2 and lspl[0] == "PROGRAMS" and lspl[1] == "*":
            final_programs_line = line
        if len(lspl) > 2 and lspl[0] == "CPU" and lspl[1] == "TIMES":
            final_CPU_line = line
    if (final_CPU_line is None) or (final_programs_line is None):
        return None
    prog_names = final_programs_line.split()[2:]
    values = [float(s) for s in final_CPU_line.split()[3:]]
    assert len(prog_names) == len(values)
    output = {}
    for prog, val in zip(prog_names, values):
        output[prog] = val
    for mand_prog in MANDATORY_PROGRAM_FIELDS:
        if mand_prog not in output:
            output[mand_prog] = float("nan")

    return output


def get_total_disk_usage(lines):
    needed_lspl = None
    for line in lines:
        lspl = line.split()
        if (
            len(lspl) > 4
            and lspl[0] == "DISK"
            and lspl[1] == "USED"
            and lspl[2] == "*"
            and lspl[-1] == "(total)"
        ):
            needed_lspl = lspl
    if needed_lspl is None:
        return None
    unit = needed_lspl[-2]
    assert unit in ["GB", "MB"]
    output = float(needed_lspl[-3])
    if unit == "MB":  # transform to GB
        output /= 1024
    return output


def calculation_results(filename):
    lines = get_file_lines(filename)
    if not calculation_converged(lines):
        return None, None, None
    return get_energies(lines), get_CPU_times(lines), get_total_disk_usage(lines)


def get_symbols_coords(filename):
    lines = get_file_lines(filename)
    geometry_started = False
    symbols = []
    coords = []
    for line in lines:
        lspl = line.split()
        if lspl == ["geometry={"]:
            geometry_started = True
            continue
        if not geometry_started:
            continue
        if lspl == ["}"]:
            return symbols, coords
        symbols.append(lspl[0])
        coords.append([float(c) for c in lspl[1:]])


atom_energy_dict = {}

cur_atom_methods = list(atom_mol_method_dict.values())


def init_atom_energy_dict():
    global atom_energy_dict
    with open("QM9IPEA_atom_ens.json", "r") as f:
        atom_energy_json = json.load(f)

    full_meth_list = None
    H = "H"

    for el, en_dict in atom_energy_json["ENERGY"].items():
        true_en_dict = {}
        for atom_meth, val in en_dict.items():
            mol_meth = atom_mol_method_dict[atom_meth]
            true_en_dict[mol_meth] = val
        atom_energy_dict[el] = true_en_dict
        if (full_meth_list is None) and (el != H):
            full_meth_list = list(true_en_dict.keys())
    # Separately brute-copy HF value for H into all other methods.
    H_val = list(atom_energy_dict[H].values())[0]
    for meth in full_meth_list:
        atom_energy_dict[H][meth] = H_val


init_atom_energy_dict()


def atomization_energy(tot_energies, method, elements):
    if tot_energies is None:
        return float("nan")
    aen = tot_energies[method]
    for el in elements:
        aen -= atom_energy_dict[el][method]
    return aen


all_xyz_subdirs = valid_xyz_subdirs(sys.argv[1])

all_coords = []

all_symbols = []

qm9_ids = []

energies = {}
CPU_times = {}
disk_usages = {}

atomization_energies = {}

for charge in charges:
    energies[charge] = {}
    CPU_times[charge] = {}
    disk_usages[charge] = []

for xyz_subdir in all_xyz_subdirs:
    qm9_ids.append(xyz_subdir_to_qm9_id(xyz_subdir))
    symbols, coords = get_symbols_coords(filename_root(xyz_subdir) + "inp")
    all_symbols.append(symbols)
    all_coords.append(coords)
    for charge in charges:
        result_file = filename_root(xyz_subdir, charge=charge) + "out"
        cur_energies, cur_CPU_times, disk_usage = calculation_results(result_file)
        if charge == 0:
            for method in cur_atom_methods:
                if method not in atomization_energies:
                    atomization_energies[method] = []
                atomization_energies[method].append(
                    atomization_energy(cur_energies, method, symbols)
                )
        if cur_energies is None:
            cur_methods = list(energies[charge].keys())
            cur_programs = list(CPU_times[charge].keys())
            assert len(cur_methods) != 0
            flnan = float("nan")
            for method in cur_methods:
                energies[charge][method].append(flnan)
            for program in cur_programs:
                CPU_times[charge][program].append(flnan)
            disk_usages[charge].append(flnan)
            continue

        for method, energy in cur_energies.items():
            if method not in energies[charge]:
                energies[charge][method] = []
            energies[charge][method].append(energy)
        for program, CPU_time in cur_CPU_times.items():
            if program not in CPU_times[charge]:
                CPU_times[charge][program] = []
            CPU_times[charge][program].append(CPU_time)
        disk_usages[charge].append(disk_usage)

final_dict = {
    "COORDS": all_coords,
    "SYMBOLS": all_symbols,
    "ENERGY": energies,
    "CPU_TIME": CPU_times,
    "DISK_USAGE": disk_usages,
    "ATOMIZATION_ENERGY": atomization_energies,
    "QM9_ID": qm9_ids,
}

with open("QM9IPEA.json", "w") as f:
    json.dump(final_dict, f)

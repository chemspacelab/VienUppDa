# Created a combined json from cleaned results dir.
import json
import os


def xyz_subdir_to_element(subdir):
    base = os.path.basename(subdir)
    bspl = base.split("_")
    return bspl[0]


def valid_xyz_subdirs(root_dir):
    return sorted([root_dir + "/" + d for d in os.listdir(root_dir)])


def xyz_subdir_out_file(subdir):
    return subdir + "/" + os.path.basename(subdir) + ".out"


def get_file_lines(filename):
    return open(filename, "r").readlines()


def calculation_converged(file_lines):
    final_line = file_lines[-1]
    final_line_spl = final_line.split()
    return final_line_spl == ["Molpro", "calculation", "terminated"]


def calculation_results(filename):
    lines = get_file_lines(filename)
    if not calculation_converged(lines):
        return None
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


def get_spin(filename):
    lines = get_file_lines(filename)
    for line in lines:
        spl = line.split(",")
        if spl[0].strip() != "wf":
            continue
        return int(spl[-1].split("=")[-1])


all_xyz_subdirs = valid_xyz_subdirs("atom_ens_upload")

spins = {}

energies = {}


for xyz_subdir in all_xyz_subdirs:
    element = xyz_subdir_to_element(xyz_subdir)
    filename = xyz_subdir_out_file(xyz_subdir)
    spins[element] = get_spin(filename)
    energies[element] = calculation_results(filename)

final_dict = {"SPIN": spins, "ENERGY": energies}

with open("QM9IPEA_atom_ens.json", "w") as f:
    json.dump(final_dict, f)

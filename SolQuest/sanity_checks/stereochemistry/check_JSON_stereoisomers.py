from rdkit import Chem
from rdkit.Chem.EnumerateStereoisomers import EnumerateStereoisomers
import sys, json, os
from tqdm import tqdm
import numpy as np
from rdkit.Chem.MolStandardize.rdMolStandardize import CanonicalTautomer
from qml2.data import NUCLEAR_CHARGE
from morfeus.conformer import ConformerEnsemble
from sortedcontainers import SortedList

heavy_elements = SortedList(list(NUCLEAR_CHARGE.keys())[1:])


class RDKitFailure(Exception):
    pass


def stereoisomer_smiles_list(SMILES):
    mol = Chem.MolFromSmiles(SMILES)
    if mol is None:
        raise RDKitFailure
    return [
        Chem.MolToSmiles(mol, isomericSmiles=True, canonical=False)
        for mol in EnumerateStereoisomers(mol)
    ]


def print_wlen(l, txt_name, len_name):
    with open(f"{txt_name}.txt", "w") as f:
        for s in l:
            print(s, file=f)
    print(f"{len_name}:", len(l))


def get_all_SMILES_from_input(f, filename):
    if (len(filename) < 6) or (filename[-5:] != ".json"):
        return [l.strip() for l in f.readlines()], None
    data_dict = json.load(f)
    if "SMILES" in data_dict:
        return data_dict["SMILES"], data_dict["ENERGY"]
    all_SMILES = []
    all_energies=[]
    for val in data_dict.values():
        all_SMILES += val["SMILES"]
        all_energies+=val["ENERGY"]
    return all_SMILES, all_energies


def get_all_SMILES(filename):
    if (len(filename) > 4) and (filename[-4:] == ".zip"):
        from zipfile import ZipFile

        zf = ZipFile(filename)
        used_filename = os.path.basename(filename[:-4])
        f = zf.open(used_filename, "r")
    else:
        used_filename = filename
        f = open(filename, "r")
    return get_all_SMILES_from_input(f, used_filename)


def get_element_map(SMILES):
    regions = []
    elements = []
    i = 0
    while i < len(SMILES):
        s = SMILES[i]
        if s == "[":
            j = i + 1
            s = SMILES[j]
            element = ""
            appending_element = True
            while s != "]":
                s = SMILES[j]
                if s in ["]", "@", "-", "+"]:
                    appending_element = False
                else:
                    if appending_element:
                        element += s
                j += 1
            regions.append((i, j))
            elements.append(element)
            i = j
            continue
        if (i < len(SMILES) - 1) and (SMILES[i : i + 2] in heavy_elements):
            regions.append((i, i + 2))
            elements.append(SMILES[i : i + 2])
            i += 2
            continue
        if s in heavy_elements:
            regions.append((i, i + 1))
            elements.append(s)
        i += 1
    return regions, elements


def get_element_map_wstereo(SMILES):
    regions, elements = get_element_map(SMILES)
    stereo = []
    for region, element in zip(regions, elements):
        if element not in ["N", "P"]:
            continue
        region_str = SMILES[region[0] : region[1]]
        if "@@" in region_str:
            stereo.append(1)
        elif "@" in region_str:
            stereo.append(0)
    return regions, elements, stereo


def filter_wsame_nitrogen(isomers):
    elements = None
    stereo = None
    filtered = []

    for i in isomers:
        _, cur_elements, cur_stereo = get_element_map_wstereo(i)
        if elements is None:
            elements = cur_elements
        else:
            assert elements == cur_elements
        if stereo is None:
            stereo = cur_stereo
        else:
            if stereo != cur_stereo:
                continue
        filtered.append(i)
    return filtered


def are_tautomers(isomers):
    true_SMILES = None
    for i in isomers:
        mol = Chem.MolFromSmiles(i)
        canon_mol = CanonicalTautomer(mol)
        canon_SMILES = Chem.CanonSmiles(
            Chem.MolToSmiles(canon_mol, isomericSmiles=True)
        )
        if true_SMILES is None:
            true_SMILES = canon_SMILES
        if true_SMILES != canon_SMILES:
            return False
    return True


def SMILES_reasonable(SMILES):
    mol = Chem.MolFromSmiles(SMILES)
    try:
        conformers = ConformerEnsemble.from_rdkit(mol, n_confs=16, optimize="MMFF94")
    except ValueError:
        return False
    return len(conformers.get_coordinates()) != 0


def only_one_reasonable(isomers):
    reasonable_found = False
    for i in isomers:
        if not SMILES_reasonable(i):
            continue
        if reasonable_found:
            return False
        reasonable_found = True
    return reasonable_found


if __name__ == "__main__":
    all_SMILES, all_energies = get_all_SMILES(sys.argv[1])

    if len(sys.argv) > 2:
        txt_prefix = f"{sys.argv[2]}_"
    else:
        txt_prefix = ""

    rdkit_failures = []
    badly_defined_SMILES = []
    stereoactive_nitrogen_SMILES = []
    stereotautomer_SMILES = []
    unreasonable_excluded_SMILES = []

    for SMILES, energy in tqdm(zip(all_SMILES, all_energies)):
        if np.isnan(energy):
            continue
        skip = False
        try:
            isomers = stereoisomer_smiles_list(SMILES)
        except RDKitFailure:
            rdkit_failures.append((SMILES, energy))
            skip = True
        if skip:
            continue
        if len(isomers) == 1:
            continue
        new_isomers = filter_wsame_nitrogen(isomers)
        if len(new_isomers) == 1:
            stereoactive_nitrogen_SMILES.append(SMILES)
            continue
        # check if discrepancy is due to tautomers
        if are_tautomers(new_isomers):
            stereotautomer_SMILES.append(SMILES)
            continue
        # check if all other isomers are unreasonable
        if only_one_reasonable(new_isomers):
            unreasonable_excluded_SMILES.append(SMILES)
            continue
        badly_defined_SMILES.append(SMILES)

    print_wlen(
        badly_defined_SMILES,
        f"{txt_prefix}badly_defined_SMILES",
        "Non-uniquely defined SMILES",
    )
    print_wlen(
        stereoactive_nitrogen_SMILES,
        f"{txt_prefix}stereoactive_nitrogen_SMILES",
        "SMILES with stereoactive nitrogen",
    )
    print_wlen(
        stereotautomer_SMILES,
        f"{txt_prefix}stereotautomer_SMILES",
        "SMILES with stereotautomers",
    )
    print_wlen(
        unreasonable_excluded_SMILES,
        f"{txt_prefix}unreasonable_excluded_SMILES",
        "SMILES without specification of unreasonable",
    )
    print_wlen(rdkit_failures, f"{txt_prefix}rdkit_failures", "RDKit failures")

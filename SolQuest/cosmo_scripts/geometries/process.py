import bz2
import collections
import glob
import os
import pdb
import pickle
import shutil
import tarfile

import numpy as np
import pandas as pd
import tqdm as tqdm

from natsort import natsorted
from qml.utils import alchemy
from rdkit import Chem
from xyz2mol import xyz2mol


# from bmapqml.utils import dump2pkl, loadpkl
def dump2pkl(obj, filename: str, compress: bool = False):
    """
    Dump an object to a pickle file.
    obj : object to be saved
    filename : name of the output file
    compress : whether bz2 library is used for compressing the file.
    """
    output_file = compress_fileopener[compress](filename, "wb")
    pickle.dump(obj, output_file)
    output_file.close()


def loadpkl(filename: str, compress: bool = False):
    """
    Load an object from a pickle file.
    filename : name of the imported file
    compress : whether bz2 compression was used in creating the loaded file.
    """
    input_file = compress_fileopener[compress](filename, "rb")
    obj = pickle.load(input_file)
    input_file.close()
    return obj


def dump2tar(obj, filename):
    """
    Dump an object to a tar file.
    obj : object to be saved
    filename : name of the output file
    """
    output_file = bz2.BZ2File(filename, "wb")
    pickle.dump(obj, output_file)
    output_file.close()
    pickle.dump(obj, open(filename, "wb"))


def loadtar(filename):
    """
    Load an object from a tar file.
    """
    input_file = bz2.BZ2File(filename, "rb")
    obj = pickle.load(input_file)
    input_file.close()
    return obj


# Atomic energies in Hartree

en_H = -0.4998382438408
en_C = -37.85108576644
en_N = -54.60094890035
en_O = -75.09380733099
en_F = -99.76879785651
en_Br = -2574.399237245
en_Cl = -460.2004121052
en_S = -398.1601326604
en_P = -341.3037861853
en_B = -24.65252240094
en_Si = -289.4032207727


ha2kcal = 627.5


def atomization_en(EN, ATOMS):
    COMP = collections.Counter(ATOMS)
    ATOMIZATION = EN - (
        COMP["H"] * en_H
        + COMP["C"] * en_C
        + COMP["N"] * en_N
        + COMP["O"] * en_O
        + COMP["F"] * en_F
        + COMP["Br"] * en_Br
        + COMP["Cl"] * en_Cl
        + COMP["S"] * en_S
        + COMP["P"] * en_P
        + COMP["B"] * en_B
        + COMP["Si"] * en_Si
    )
    return ATOMIZATION * ha2kcal


def Cosmo2xyz(filename):
    conf_data = {}
    filepath = open(filename, "r")
    Lines = np.array(filepath.readlines())
    Nat = np.int(Lines[0])
    energy = float(Lines[1].split(";")[0].split("=")[1])
    method = str(Lines[1].split(";")[1].split("=")[1])
    basis = str(Lines[1].split(";")[2].split("=")[1])
    q_crds = Lines[2 : Nat + 2]
    Q, R = [], []
    for l in q_crds:
        Q.append(l.split()[0])
        R.append([float(l.split()[1]), float(l.split()[2]), float(l.split()[3])])

    R = np.array(R)
    atomization = atomization_en(energy, Q)
    charge = float(Lines[Nat + 4].strip())
    if len(Lines) > Nat + 6:
        dipole = np.float_(Lines[Nat + 6 :][0].strip().split(" "))

    else:
        dipole = np.zeros(4)

    conf_data["Q"], conf_data["R"] = Q, R.tolist()
    conf_data["charge"], conf_data["dipole"] = charge, dipole.tolist()
    (
        conf_data["energy"],
        conf_data["method"],
        conf_data["basis"],
        conf_data["atomization"],
    ) = (
        energy,
        method,
        basis,
        atomization,
    )
    return conf_data


def read_file_line_by_line(filename):
    """
    Read file with strings line by line
    and append to a list and remove the newline character
    """

    with open(filename, "r") as f:
        lines = f.readlines()
    lines = [x.strip() for x in lines]
    return lines


def process_archive(unpack_path, name_archive, nametag, processed_path):
    dst_dir = "/data/jan/calculations/tmp/"
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    if nametag == "gdb17":
        files = glob.glob(unpack_path + "/*")

        for file in files:
            src_dir = file + "/Results_of_BP-TZVPD-FINE-COSMO/"
            # copy all
            for fi in glob.glob(src_dir + "/*"):
                shutil.copy(fi, dst_dir)

    elif nametag == "amons_GDB17" or nametag == "amons_ZINC":
        files = glob.glob(unpack_path + "/*")
        for file in files:
            shutil.copy(file, dst_dir)

    elif nametag == "EGP":
        print(unpack_path)
        files = glob.glob(unpack_path + "/*")
        for file in files:
            shutil.copy(file, dst_dir)

    else:
        print("Unknown archive type")

    # pdb.set_trace()
    data_dir = dst_dir + "*_c0*"
    files = sorted(glob.glob(data_dir))
    if nametag == "amons_GDB17":
        allMols = natsorted(
            np.array(
                [
                    "AG7_" + f.split("/")[-1].split(".")[0].split("_")[1]
                    for f in files
                    if "cosmo" in f
                ]
            )
        )
        free_energies_dir = "/data/jan/calculations/database/AMONS/GDB17/FRGS/solvents"

    if nametag == "amons_ZINC":
        allMols = natsorted(
            np.array(
                [
                    "AZ7_" + f.split("/")[-1].split(".")[0].split("_")[1]
                    for f in files
                    if "cosmo" in f
                ]
            )
        )
        free_energies_dir = "/data/jan/calculations/database/AMONS/ZINC/FRGS/solvents"

    if nametag == "FreeSolv":
        allMols = natsorted(
            np.array(
                [
                    "mobley_" + f.split("/")[-1].split(".")[0].split("_")[1]
                    for f in files
                    if "cosmo" in f
                ]
            )
        )

    if nametag == "gdb17":
        GDB17_smiles = read_file_line_by_line(
            "/data/jan/calculations/database/GDB17/GDB17.50000000.smi"
        )
        allMols = natsorted(
            np.array(
                [
                    f.split("/")[-1].split(".")[0].split("_")[0]
                    for f in files
                    if "cosmo" in f
                ]
            )
        )
        free_energies_dir = "/data/jan/calculations/database/GDB17/FRGS/solvents"
    if nametag == "EGP":
        allMols = natsorted(
            np.array(
                [
                    f.split("/")[-1].split(".")[0].split("_")[0]
                    for f in files
                    if "cosmo" in f
                ]
            )
        )
        # natsorted(np.array(["mobley_"+f.split("/")[-1].split(".")[0].split("_")[1] for f in files if "cosmo" in f]))
        free_energies_dir = "/data/jan/calculations/database/EGP/FRGS/solvents/part-2"

    all_data = {}
    data = {}
    for mol in tqdm.tqdm(allMols):
        mol_data = {}
        try:
            CONFORMERS = glob.glob(dst_dir + f"/{mol}_c*.energy")
            CONFORMERS = natsorted(CONFORMERS)

            if nametag == "amons_GDB17":
                molname = CONFORMERS[0].split("/")[-1].split("_")
                molname = molname[0] + "_" + molname[1]

            if nametag == "amons_ZINC":
                molname = CONFORMERS[0].split("/")[-1].split("_")
                molname = molname[0] + "_" + molname[1]

            if nametag == "FreeSolv":
                molname = CONFORMERS[0].split("/")[-1].split("_")
                molname = molname[0] + "_" + molname[1]

            if nametag == "gdb17":
                molname = str(CONFORMERS[0].split("/")[-1].split("_")[0])
                original_smiles = GDB17_smiles[int(molname) - 1]

            if nametag == "EGP":
                molname = str(CONFORMERS[0].split("/")[-1].split("_")[0])

            for ind, conf in enumerate(CONFORMERS):
                new_dict = Cosmo2xyz(conf)
                mol_data["c{}".format(ind)] = new_dict
                if ind == 0:
                    try:
                        charges = [
                            alchemy.NUCLEAR_CHARGE[el] for el in mol_data["c0"]["Q"]
                        ]
                        coords = mol_data["c0"]["R"]

                        rdkit_mol = xyz2mol(charges, coords)[0]
                        smi_extracted = Chem.MolToSmiles(
                            Chem.RemoveHs(rdkit_mol), canonical=True
                        )

                    except:
                        print("Error with xyz2mol")
                        mol = None

            if nametag == "gdb17":
                mol_data["SMILES_GDB17"] = original_smiles
            mol_data["SMILES_extracted"] = smi_extracted
            data["{}".format(molname)] = mol_data

        except:
            print(f"Failed to process {mol}")

    pdb.set_trace()
    if "EGP-part" not in name_archive:
        solvation_energies_loc = f"{free_energies_dir}/*{name_archive}_*.csv"
    else:
        solvation_energies_loc = f"{free_energies_dir}/*.csv"

    for solv in glob.glob(solvation_energies_loc):
        # load csv file to pandas dataframe

        solv_name = solv.split("/")[-1].split("_")[-1]

        try:
            solvent_data = pd.read_csv(solv)
            # remove douplicate rows with same "Compound" name
            solvent_data = solvent_data.drop_duplicates(subset="Compound", keep="first")

            for solute, dG in zip(solvent_data["Compound"], solvent_data["Gsolv"]):
                if str(solute) in data:
                    data[str(solute)]["{}".format(solv_name.split(".")[0])] = dG
                else:
                    print(
                        "Solvation energy not found in xyz dataset for {}".format(
                            solute
                        )
                    )
        except:
            print("Failed to load {}".format(solv))
    # pdb.set_trace()
    # pdb.set_trace()
    all_data["{}".format(nametag)] = data
    dump2pkl(all_data, "{}/{}_{}.pkl".format(processed_path, nametag, name_archive))
    # remove dst_dir now
    shutil.rmtree(dst_dir)


def merge_dicts(dict1, dict2):
    """
    Recursively merges two dictionaries and their sub-dictionaries.
    """
    # Check if both arguments are dictionaries.
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        # Create a new dictionary to store the merged key-value pairs.
        merged_dict = {}

        # Get all keys from both dictionaries.
        keys = set(dict1.keys()) | set(dict2.keys())

        # Merge the key-value pairs with the same key recursively.
        for key in keys:
            value1 = dict1.get(key)
            value2 = dict2.get(key)

            if isinstance(value1, dict) and isinstance(value2, dict):
                merged_dict[key] = merge_dicts(value1, value2)
            else:
                merged_dict[key] = value2 if value2 is not None else value1

        return merged_dict
    else:
        raise TypeError("Arguments must be dictionaries.")


if __name__ == "__main__":
    PROCESS, MERGE = True, False

    nametag = "EGP"  # "amons_ZINC" #"gdb17"
    if PROCESS:
        if nametag == "EGP":
            archive_path = "/data/jan/calculations/database/EGP/leruli_run/results_2nd/Results_of_BP-TZVPD-FINE-COSMO"
            # "/data/jan/calculations/database/EGP/leruli_run/part-1"
            # "/data/jan/calculations/database/EGP/leruli_run/part-1"
            # ALL_UNPACK_PATH = "/store/jan/calculations/EGP/processing/part-2"
            processed_path = "/store/jan/calculations/EGP/part-1/processed/part-2"

            natsorted(glob.glob(f"{archive_path}"))
            NAME_ARCHIVE = "EGP-part2"
            ALL_UNPACK_PATH = archive_path
            CURR_UNPACK_PATH = ALL_UNPACK_PATH

            process_archive(CURR_UNPACK_PATH, NAME_ARCHIVE, nametag, processed_path)

        if nametag == "gd17":
            archive_path = "/data/jan/calculations/database/GDB17/vsc/packed/*.tar.gz"
            ALL_UNPACK_PATH = "/data/jan/calculations/database/GDB17/vsc/processing"
            processed_path = "/data/jan/calculations/database/GDB17/vsc/processed"

            tarfiles = glob.glob(f"{archive_path}")
            # extract all tar files
            print(tarfiles)

            for ball in tarfiles:
                print(ball)

                try:
                    tar = tarfile.open(ball)
                    tar.extractall(path=ALL_UNPACK_PATH)
                    tar.close()

                    NAME_ARCHIVE = ball.split("/")[-1].split(".")[0]
                    CURR_UNPACK_PATH = ALL_UNPACK_PATH + "/" + NAME_ARCHIVE
                    process_archive(
                        CURR_UNPACK_PATH, NAME_ARCHIVE, nametag, processed_path
                    )
                    shutil.rmtree(CURR_UNPACK_PATH)
                except:
                    print("Failed to process {}".format(ball))

        if nametag == "amons_GDB17":
            archive_path = "/data/jan/calculations/database/AMONS/GDB17/Results_of_BP-TZVPD-FINE-COSMO/*"
            ALL_UNPACK_PATH = "/data/jan/calculations/database/AMONS/GDB17/processing"
            processed_path = "/data/jan/calculations/database/AMONS/GDB17/processed"
            for ni in natsorted(glob.glob(archive_path)):  # [:4]:
                # print(ni)
                # test of ni contains subfolders
                if len(glob.glob(f"{ni}/part-*")) > 0:
                    for nj in natsorted(glob.glob(f"{ni}/part-*")):
                        # print(nj)

                        NAME_ARCHIVE = "{}_{}".format(
                            ni.split("/")[-1], nj.split("/")[-1]
                        )
                        ALL_FILES = os.listdir(nj)
                        print(NAME_ARCHIVE)
                        CURR_UNPACK_PATH = ALL_UNPACK_PATH + "/" + NAME_ARCHIVE
                        if not os.path.exists(CURR_UNPACK_PATH):
                            os.makedirs(CURR_UNPACK_PATH)
                        for file in ALL_FILES:
                            # pdb.set_trace()
                            shutil.copy(f"{nj}/{file}", f"{CURR_UNPACK_PATH}/{file}")

                        process_archive(
                            CURR_UNPACK_PATH, NAME_ARCHIVE, nametag, processed_path
                        )
                        shutil.rmtree(CURR_UNPACK_PATH)
                        # pdb.set_trace()

                else:
                    NAME_ARCHIVE = ni.split("/")[-1]
                    ALL_FILES = os.listdir(ni)
                    CURR_UNPACK_PATH = ALL_UNPACK_PATH + "/" + NAME_ARCHIVE
                    print(CURR_UNPACK_PATH)
                    if not os.path.exists(CURR_UNPACK_PATH):
                        os.makedirs(CURR_UNPACK_PATH)

                    print(ALL_FILES)
                    for file in ALL_FILES:
                        shutil.copy(f"{ni}/{file}", f"{CURR_UNPACK_PATH}/{file}")
                    # TODO: process archive
                    process_archive(
                        CURR_UNPACK_PATH, NAME_ARCHIVE, nametag, processed_path
                    )
                    print(CURR_UNPACK_PATH)
                    shutil.rmtree(CURR_UNPACK_PATH)
            # pdb.set_trace()

        if nametag == "amons_ZINC":
            archive_path = "/data/jan/calculations/database/AMONS/ZINC/Results_of_BP-TZVPD-FINE-COSMO/*"
            ALL_UNPACK_PATH = "/data/jan/calculations/database/AMONS/ZINC/processing"
            processed_path = "/data/jan/calculations/database/AMONS/ZINC/processed"
            for ni in natsorted(glob.glob(archive_path))[1:]:  # [:4]:
                if len(glob.glob(f"{ni}/part-*")) > 0:
                    for nj in natsorted(glob.glob(f"{ni}/part-*")):
                        print(nj)

                        NAME_ARCHIVE = "{}_{}".format(
                            ni.split("/")[-1], nj.split("/")[-1]
                        )
                        ALL_FILES = os.listdir(nj)
                        CURR_UNPACK_PATH = ALL_UNPACK_PATH + "/" + NAME_ARCHIVE
                        if not os.path.exists(CURR_UNPACK_PATH):
                            os.makedirs(CURR_UNPACK_PATH)
                        for file in ALL_FILES:
                            # pdb.set_trace()
                            shutil.copy(f"{nj}/{file}", f"{CURR_UNPACK_PATH}/{file}")

                        process_archive(
                            CURR_UNPACK_PATH, NAME_ARCHIVE, nametag, processed_path
                        )
                        shutil.rmtree(CURR_UNPACK_PATH)
                else:
                    NAME_ARCHIVE = ni.split("/")[-1]
                    ALL_FILES = os.listdir(ni)
                    CURR_UNPACK_PATH = ALL_UNPACK_PATH + "/" + NAME_ARCHIVE
                    print(CURR_UNPACK_PATH)

                    if not os.path.exists(CURR_UNPACK_PATH):
                        os.makedirs(CURR_UNPACK_PATH)

                    print(ALL_FILES)

                    for file in ALL_FILES:
                        shutil.copy(f"{ni}/{file}", f"{CURR_UNPACK_PATH}/{file}")

                    # TODO: process archive
                    process_archive(
                        CURR_UNPACK_PATH, NAME_ARCHIVE, nametag, processed_path
                    )
                    print(CURR_UNPACK_PATH)
                    shutil.rmtree(CURR_UNPACK_PATH)
    if MERGE:
        # merge all pickle files
        if nametag == "gd17":
            processed_path = "/data/jan/calculations/database/GDB17/vsc/processed"
        if nametag == "amons_GDB17":
            processed_path = "/data/jan/calculations/database/AMONS/GDB17/processed"
        if nametag == "amons_ZINC":
            processed_path = "/data/jan/calculations/database/AMONS/ZINC/processed"

        all_data = {}
        for pkl in glob.glob(f"{processed_path}/*.pkl"):
            data = loadpkl(pkl)
            # pdb.set_trace()
            # all_data = {**all_data,**data}
            all_data = merge_dicts(all_data, data)
        dump2pkl(all_data, f"{processed_path}/all_data_{nametag}.pkl")
        pdb.set_trace()


"""

Modify program such that it can be used for AMONS data in the following file structure:
AMONS GDB17:

jan@o:/data/jan/calculations/database/AMONS/GDB17/FRGS/solvents$

AMONS_GDB17_ni4_cyclohexane.csv              AMONS_GDB17_ni7_part-2_thf.csv
AMONS_GDB17_ni4_diethyleneglycol.csv         AMONS_GDB17_ni7_part-2_toluene.csv
AMONS_GDB17_ni4_diethylether.csv             AMONS_GDB17_ni7_part-2_triethylamine.csv
AMONS_GDB17_ni4_diglyme.csv                  AMONS_GDB17_ni7_part-3_1-octanol.csv
AMONS_GDB17_ni4_dimethylsulfoxide.csv




AG7_08874_c5.cosmo        AG7_19440_c2.energy.xyz   AG7_30726_c0.energy.xyz   AG7_41424_c0.energy
AG7_08874_c5.energy       AG7_19441_c0.cosmo        AG7_30726_c1.cosmo        AG7_41424_c0.energy.xyz
AG7_08874_c5.energy.xyz   AG7_19441_c0.energy       AG7_30726_c1.energy
AG7_08874_c6.cosmo        AG7_19441_c0.energy.xyz   AG7_30726_c1.energy.xyz
jan@o:/data/jan/calculations/database/AMONS/GDB17/Results_of_BP-TZVPD-FINE-COSMO/ni7/part-3$


AMONS ZINC:

AMONS_ZINC_ni6_part-2_chcl3.csv                    AMONS_ZINC_ni7_part-5_propanone.csv
AMONS_ZINC_ni6_part-2_chlorobenzene.csv            AMONS_ZINC_ni7_part-5_pyridine.csv
AMONS_ZINC_ni6_part-2_cyclohexane.csv              AMONS_ZINC_ni7_part-5_thf.csv
AMONS_ZINC_ni6_part-2_diethyleneglycol.csv         AMONS_ZINC_ni7_part-5_toluene.csv
AMONS_ZINC_ni6_part-2_diethylether.csv             AMONS_ZINC_ni7_part-5_triethylamine.csv
AMONS_ZINC_ni6_part-2_diglyme.csv
jan@o:/data/jan/calculations/database/AMONS/ZINC/FRGS/solvents$ pwd
AZ7_28455_c0.energy   AZ7_43983_c1.energy   AZ7_60818_c6.cosmo    AZ7_77123_c4.energy   AZ7_98151_c1.energy
AZ7_28455_c1.cosmo    AZ7_43983_c2.cosmo    AZ7_60818_c6.energy   AZ7_77124_c0.cosmo    AZ7_98151_c2.cosmo
AZ7_28455_c1.energy   AZ7_43983_c2.energy   AZ7_60818_c7.cosmo    AZ7_77124_c0.energy   AZ7_98151_c2.energy
AZ7_28455_c2.cosmo    AZ7_43983_c3.cosmo    AZ7_60818_c7.energy   AZ7_77124_c1.cosmo    AZ7_98151_c3.cosmo
AZ7_28455_c2.energy   AZ7_43983_c3.energy   AZ7_60818_c8.cosmo    AZ7_77124_c1.energy   AZ7_98151_c3.energy
jan@o:/data/jan/calculations/database/AMONS/ZINC/Results_of_BP-TZVPD-FINE-COSMO/ni7/part-1$ pwd

"""

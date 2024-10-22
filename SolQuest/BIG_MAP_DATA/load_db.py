import json
import pdb

import numpy as np


class Load_datasets:
    def __init__(self, dataset_name="EGP"):
        if dataset_name == "EGP":
            self.load_json("./post_processed/EGP.json")
        elif dataset_name == "GDB17":
            self.load_json("./post_processed/GDB17.json")
        elif dataset_name == "AMONS_ZINC":
            self.load_json("./post_processed/AMONS_ZINC.json")
        elif dataset_name == "AMONS_GDB17":
            self.load_json("./post_processed/AMONS_GDB17.json")
        else:
            raise NotImplementedError

    def load_json(self, path):
        with open(path, "r") as f:
            self.data = json.load(f)


if __name__ == "__main__":
    # For example load EGP dataset
    loader = Load_datasets("EGP")
    EGP_data = loader.data
    # Extract ECFP Fingerprints
    X = np.array(EGP_data["ECFP"])
    # Extract SMILES
    SMILES = EGP_data["SMILES"]
    # Extract Symbols
    SYMBOLS = EGP_data["SYMBOLS"]
    # Extract Coordinates, including conformers, ordered by energy
    COORDS = np.array(EGP_data["COORDS"])
    # For instance this entry has 16 conformers
    print("(#conformers, #atoms, #coordinates)")
    print(np.array(COORDS[100]).shape)
    # Extract Atomization energies, again also ordered by energy and for each conformer
    ATOMIZATION = np.array(EGP_data["ATOMIZATION"])
    # Extract Dipole moments
    DIPOLE = np.array(EGP_data["DIPOLE"])
    # Note that the first entry is the total dipole moment of each conformer (vector norm)
    print(np.array(DIPOLE[100])[0])
    # the second entry is the dipole moment vector of the each conformer
    print(np.array(DIPOLE[100])[1])
    # Extract Energies, (only the lowest energy conformer)
    ENERGY = np.array(EGP_data["ENERGY"])
    # Extract Solvation energies
    SOLVATION = EGP_data["SOLVATION"]
    # get the solvation energy for solvent water and molecule 100
    print(SOLVATION["h2o"][100])
    # print a list of all availible solvents
    print(SOLVATION.keys())
    print("number of molecules in EGP dataset: ", len(SMILES))

    pdb.set_trace()

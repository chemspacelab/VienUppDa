import json
import numpy as np
import pdb

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

    dataset_name = "GDB17"
    loader = Load_datasets(dataset_name)
    DATA = loader.data

    if "AMONS" in dataset_name:
        nr_amons = 0
        for key in DATA.keys():
            # pdb.set_trace()
            SUBDATA = DATA[key]

            # Extract ECFP Fingerprints
            X = np.array(SUBDATA["ECFP"])
            # Extract SMILES
            SMILES = SUBDATA["SMILES"]
            # Extract Symbols
            SYMBOLS = SUBDATA["SYMBOLS"]
            # Extract Coordinates, including conformers, ordered by energy
            COORDS = SUBDATA["COORDS"]
            # Extract Atomization energies, again also ordered by energy and for each conformer
            ATOMIZATION = SUBDATA["ATOMIZATION"]
            # Extract Dipole moments
            DIPOLE = SUBDATA["DIPOLE"]
            # Extract Energies, (only the lowest energy conformer)
            ENERGY = np.array(SUBDATA["ENERGY"])
            # Extract Solvation energies
            SOLVATION = SUBDATA["SOLVATION"]
            # get the solvation energy for solvent water and molecule 100
            print("number of molecules in {} dataset: ".format(dataset_name), len(SMILES))

            nr_amons += len(SMILES)

        print("number of amons in {} dataset: ".format(dataset_name), nr_amons)

    else:

        X = np.array(DATA["ECFP"])
        # Extract SMILES
        SMILES = DATA["SMILES"]
        # Extract Symbols
        SYMBOLS = DATA["SYMBOLS"]
        # Extract Coordinates, including conformers, ordered by energy
        COORDS = DATA["COORDS"]
        # Extract Atomization energies, again also ordered by energy and for each conformer
        ATOMIZATION = DATA["ATOMIZATION"]
        # Extract Dipole moments
        DIPOLE = DATA["DIPOLE"]
        # Extract Energies, (only the lowest energy conformer)
        ENERGY = np.array(DATA["ENERGY"])
        # Extract Solvation energies
        SOLVATION = DATA["SOLVATION"]
        # get the solvation energy for solvent water and molecule 100
        print("number of molecules in {} dataset: ".format(dataset_name), len(SMILES))
        #pdb.set_trace()

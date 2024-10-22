from utils_db import (
    combine_dictionaries,
    extract_EGP,
    extract_GDB17,
    find_unique_indices,
    load_EGP,
    load_GDB17,
    np,
    save_dict_to_json,
)

if __name__ == "__main__":
    do_EGP, do_GDB17 = True, True

    if do_EGP:
        all_egp_1, all_egp_2 = load_EGP()
        (
            X_1,
            SYMBOLS_1,
            COORDS_1,
            SMILES_1,
            ATOMIZATION_1,
            ENERGY_1,
            SOLVATION_1,
            DIPOLE_1,
        ) = extract_EGP(all_egp_1)
        (
            X_2,
            SYMBOLS_2,
            COORDS_2,
            SMILES_2,
            ATOMIZATION_2,
            ENERGY_2,
            SOLVATION_2,
            DIPOLE_2,
        ) = extract_EGP(all_egp_2)

        SYMBOLS = np.concatenate((SYMBOLS_1, SYMBOLS_2))
        SMILES = np.concatenate((SMILES_1, SMILES_2))
        COORDS = np.concatenate((COORDS_1, COORDS_2))
        X = np.concatenate((X_1, X_2))
        SOLVATION = combine_dictionaries(SOLVATION_1, SOLVATION_2)
        ATOMIZATION = np.concatenate((ATOMIZATION_1, ATOMIZATION_2))
        DIPOLE = np.concatenate((DIPOLE_1, DIPOLE_2))
        ENERGY = np.concatenate((ENERGY_1, ENERGY_2))

        UNIQUE = find_unique_indices(SMILES)

        X = X[UNIQUE]
        SMILES = SMILES[UNIQUE]
        SYMBOLS = SYMBOLS[UNIQUE]
        COORDS = COORDS[UNIQUE]
        ATOMIZATION = ATOMIZATION[UNIQUE]
        DIPOLE = DIPOLE[UNIQUE]
        ENERGY = ENERGY[UNIQUE]
        SOLVATION_NEW = {}
        for key in SOLVATION.keys():
            SOLVATION_NEW[key] = SOLVATION[key][UNIQUE]

        EGP_data_dict = {
            "ECFP": X,
            "SMILES": SMILES,
            "SYMBOLS": SYMBOLS,
            "COORDS": COORDS,
            "ATOMIZATION": ATOMIZATION,
            "DIPOLE": DIPOLE,
            "ENERGY": ENERGY,
            "SOLVATION": SOLVATION_NEW,
        }

        # save as json
        save_dict_to_json(EGP_data_dict, "./post_processed/EGP.json")

    if do_GDB17:
        GDB17_1, GDB17_2 = load_GDB17(filename=1), load_GDB17(filename=2)
        (
            X_1,
            SYMBOLS_1,
            COORDS_1,
            SMILES_1,
            ATOMIZATION_1,
            ENERGY_1,
            SOLVATION_1,
            DIPOLE_1,
        ) = extract_GDB17(GDB17_1)

        (
            X_2,
            SYMBOLS_2,
            COORDS_2,
            SMILES_2,
            ATOMIZATION_2,
            ENERGY_2,
            SOLVATION_2,
            DIPOLE_2,
        ) = extract_GDB17(GDB17_2)

        SYMBOLS = np.concatenate((SYMBOLS_1, SYMBOLS_2))
        SMILES = np.concatenate((SMILES_1, SMILES_2))
        COORDS = np.concatenate((COORDS_1, COORDS_2))
        X = np.concatenate((X_1, X_2))
        SOLVATION = combine_dictionaries(SOLVATION_1, SOLVATION_2)
        ATOMIZATION = np.concatenate((ATOMIZATION_1, ATOMIZATION_2))
        DIPOLE = np.concatenate((DIPOLE_1, DIPOLE_2))
        ENERGY = np.concatenate((ENERGY_1, ENERGY_2))

        UNIQUE = find_unique_indices(SMILES)

        X = X[UNIQUE]
        SMILES = SMILES[UNIQUE]
        SYMBOLS = SYMBOLS[UNIQUE]
        COORDS = COORDS[UNIQUE]
        ATOMIZATION = ATOMIZATION[UNIQUE]
        DIPOLE = DIPOLE[UNIQUE]
        ENERGY = ENERGY[UNIQUE]
        SOLVATION_NEW = {}
        for key in SOLVATION.keys():
            SOLVATION_NEW[key] = SOLVATION[key][UNIQUE]

        GDB17_data_dict = {
            "ECFP": X,
            "SMILES": SMILES,
            "SYMBOLS": SYMBOLS,
            "COORDS": COORDS,
            "ATOMIZATION": ATOMIZATION,
            "DIPOLE": DIPOLE,
            "ENERGY": ENERGY,
            "SOLVATION": SOLVATION_NEW,
        }

        # save as json
        save_dict_to_json(GDB17_data_dict, "./post_processed/GDB17.json")

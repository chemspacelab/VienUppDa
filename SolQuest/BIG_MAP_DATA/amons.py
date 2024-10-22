from utils_db import (
    extract_amons_zinc,
    extract_gdb17_amons,
    load_amons_gdb17,
    load_amons_zinc,
    save_dict_to_json,
)

if __name__ == "__main__":
    amons_zinc = load_amons_zinc()

    amon_zinc_dict = {}
    for amon_dim in list(amons_zinc.keys()):
        (
            X,
            SYMBOLS,
            COORDS,
            SMILES,
            ATOMIZATION,
            ENERGY,
            SOLVATION,
            DIPOLE,
        ) = extract_amons_zinc(amons_zinc, amon_file=amon_dim)

        amon_zinc_dict[amon_dim] = {
            "ECFP": X,
            "SMILES": SMILES,
            "SYMBOLS": SYMBOLS,
            "COORDS": COORDS,
            "ATOMIZATION": ATOMIZATION,
            "DIPOLE": DIPOLE,
            "ENERGY": ENERGY,
            "SOLVATION": SOLVATION,
        }

    save_dict_to_json(amon_zinc_dict, "./post_processed/AMONS_ZINC.json")

    amon_gdb17_data = load_amons_gdb17()

    amon_gdb17_dict = {}
    for amon_dim in list(amon_gdb17_data.keys()):
        (
            X,
            SYMBOLS,
            COORDS,
            SMILES,
            ATOMIZATION,
            ENERGY,
            SOLVATION,
            DIPOLE,
        ) = extract_gdb17_amons(amon_gdb17_data, amon_file=amon_dim)

        amon_gdb17_dict[amon_dim] = {
            "ECFP": X,
            "SMILES": SMILES,
            "SYMBOLS": SYMBOLS,
            "COORDS": COORDS,
            "ATOMIZATION": ATOMIZATION,
            "DIPOLE": DIPOLE,
            "ENERGY": ENERGY,
            "SOLVATION": SOLVATION,
        }

    save_dict_to_json(amon_gdb17_dict, "./post_processed/AMONS_GDB17.json")

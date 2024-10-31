import json
import re

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import umap
from qml2.data import NUCLEAR_CHARGE
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.decomposition import IncrementalPCA
from xyz2mol import xyz2mol

solvent_list = """
1,2-dichloroethane
2-butanol
acetonitrile
thf
ch2cl2
h2o
aceticacid
hexane
diethylether
propanone
1-butanol
diglyme
nitromethane
pyridine
cyclohexane
ccl4
dioxane
ethylacetate
toluene
chcl3
n-heptane
1,2-dimethylbenzene
pentane
chlorobenzene
diethyleneglycol
dimethylsulfoxide
butanone
hexamethylphosphoramide
benzene
methanol
glycerol
1-octanol
triethylamine
1,4-dimethylbenzene
glycol
propanol
1,3-dimethylbenzene
ethanol
2-propanol
"""
solvent_names = solvent_list.strip().split("\n")
solvent_names_array = np.array(solvent_names)

ADMITTED_ELEMENTS = {"O", "Si", "Br", "C", "S", "N", "P", "F", "B", "H", "Cl"}


def load_amons_gdb17():
    with open("all_amons_gdb17.json", "r") as f:
        all_amons_gdb17 = json.load(f)
    return all_amons_gdb17


def load_amons_zinc():
    with open("all_amons_zinc.json", "r") as f:
        all_amons_zinc = json.load(f)
    return all_amons_zinc


def extract_amons_zinc(amon_data, amon_file="ni1"):
    names = amon_data[amon_file]["data"]["amons_ZINC"].keys()
    SYMBOLS = []
    COORDS = []
    SMILES = []
    ENERGY = []
    ATOMIZATION = []
    SOLVATION = []
    DIPOLE = []
    X = []
    for name in names:
        try:
            cnfs = find_cnumber_keys(amon_data[amon_file]["data"]["amons_ZINC"][name])
            symbols = amon_data[amon_file]["data"]["amons_ZINC"][name]["c0"]["Q"]
            nuc_q = symbols2nuclear_charges(symbols)
            coords = np.array(amon_data[amon_file]["data"]["amons_ZINC"][name]["c0"]["R"])
            dipole = [
                [amon_data[amon_file]["data"]["amons_ZINC"][name][cn]["dipole"][0] for cn in cnfs],
                [
                    amon_data[amon_file]["data"]["amons_ZINC"][name][cn]["dipole"][1:]
                    for cn in cnfs
                ],
            ]
            charge = amon_data[amon_file]["data"]["amons_ZINC"][name]["c0"]["charge"]
            smiles = np.nan
            smiles = extract_smiles(nuc_q, coords, charge)

            check_charge = check_connected_charged(smiles)
            check_elements = check_if_in_dictionary(symbols)
            if check_elements and check_charge:
                CURR_SOLV = []
                for solv in solvent_names_array:
                    try:
                        value = amon_data[amon_file]["data"]["amons_ZINC"][name][solv]
#                        if value < 30 and value > -80:
                        CURR_SOLV.append(value)
#                        else:
#                            CURR_SOLV.append(np.nan)
                    except:
                        CURR_SOLV.append(np.nan)
                SOLVATION.append(CURR_SOLV)
                SMILES.append(smiles)
                ATOMIZATION.append(
                    [
                        amon_data[amon_file]["data"]["amons_ZINC"][name][cn]["atomization"]
                        for cn in cnfs
                    ]
                )
                COORDS.append(
                    [amon_data[amon_file]["data"]["amons_ZINC"][name][cn]["R"] for cn in cnfs]
                )
                ENERGY.append(amon_data[amon_file]["data"]["amons_ZINC"][name]["c0"]["energy"])
                SYMBOLS.append(symbols)
                DIPOLE.append(dipole)
                X.append(smiles_to_fingerprint(smiles))
        except:
            pass

    X, SYMBOLS, COORDS, SMILES, ATOMIZATION, ENERGY, SOLVATION, DIPOLE = (
        np.array(X),
        SYMBOLS,
        COORDS,
        SMILES,
        ATOMIZATION,
        np.array(ENERGY),
        np.array(SOLVATION),
        DIPOLE,
    )

    SOLV_DATA = {}
    for ind, name in enumerate(solvent_names_array):
        SOLV_DATA[name] = SOLVATION[:, ind]

    return (
        X,
        SYMBOLS,
        COORDS,
        SMILES,
        ATOMIZATION,
        ENERGY,
        SOLV_DATA,
        DIPOLE,
    )


def extract_gdb17_amons(amon_data, amon_file="ni1"):
    names = amon_data[amon_file]["data"]["amons_GDB17"].keys()
    SYMBOLS = []
    COORDS = []
    SMILES = []
    ENERGY = []
    ATOMIZATION = []
    SOLVATION = []
    DIPOLE = []
    X = []
    for name in names:
        try:
            cnfs = find_cnumber_keys(amon_data[amon_file]["data"]["amons_GDB17"][name])
            symbols = amon_data[amon_file]["data"]["amons_GDB17"][name]["c0"]["Q"]
            nuc_q = symbols2nuclear_charges(symbols)
            coords = np.array(amon_data[amon_file]["data"]["amons_GDB17"][name]["c0"]["R"])
            dipole = [
                [
                    amon_data[amon_file]["data"]["amons_GDB17"][name][cn]["dipole"][0]
                    for cn in cnfs
                ],
                [
                    amon_data[amon_file]["data"]["amons_GDB17"][name][cn]["dipole"][1:]
                    for cn in cnfs
                ],
            ]
            charge = amon_data[amon_file]["data"]["amons_GDB17"][name]["c0"]["charge"]
            smiles = np.nan
            smiles = extract_smiles(nuc_q, coords, charge)

            check_charge = check_connected_charged(smiles)
            check_elements = check_if_in_dictionary(symbols)
            if check_elements and check_charge:
                CURR_SOLV = []
                for solv in solvent_names_array:
                    try:
                        value = amon_data[amon_file]["data"]["amons_GDB17"][name][solv]
#                        if value < 30 and value > -80:
#                            CURR_SOLV.append(value)
                        CURR_SOLV.append(value)
#                        else:
#                            CURR_SOLV.append(np.nan)
                    except:
                        CURR_SOLV.append(np.nan)

                SOLVATION.append(CURR_SOLV)
                SMILES.append(smiles)
                ATOMIZATION.append(
                    [
                        amon_data[amon_file]["data"]["amons_GDB17"][name][cn]["atomization"]
                        for cn in cnfs
                    ]
                )
                COORDS.append(
                    [amon_data[amon_file]["data"]["amons_GDB17"][name][cn]["R"] for cn in cnfs]
                )
                ENERGY.append(amon_data[amon_file]["data"]["amons_GDB17"][name]["c0"]["energy"])
                SYMBOLS.append(symbols)
                DIPOLE.append(dipole)
                X.append(smiles_to_fingerprint(smiles))
        except:
            pass

    X, SYMBOLS, COORDS, SMILES, ATOMIZATION, ENERGY, SOLVATION, DIPOLE = (
        np.array(X),
        SYMBOLS,
        COORDS,
        SMILES,
        ATOMIZATION,
        np.array(ENERGY),
        np.array(SOLVATION),
        DIPOLE,
    )

    SOLV_DATA = {}
    for ind, name in enumerate(solvent_names_array):
        SOLV_DATA[name] = SOLVATION[:, ind]

    return (
        X,
        SYMBOLS,
        COORDS,
        SMILES,
        ATOMIZATION,
        ENERGY,
        SOLV_DATA,
        DIPOLE,
    )


def load_EGP():
    with open("egp_1.json", "r") as f:
        all_egp_1 = json.load(f)

    with open("egp_2.json", "r") as f:
        all_egp_2 = json.load(f)
    return all_egp_1, all_egp_2


def load_GDB17(filename=1):
    if filename == 1:
        with open("all_gdb17_1.json", "r") as f:
            all_GDB17 = json.load(f)
        return all_GDB17
    elif filename == 2:
        with open("all_gdb17_2.json", "r") as f:
            all_GDB17 = json.load(f)
        return all_GDB17
    else:
        print("Wrong filename")


def check_if_in_dictionary(symbols):
    all_in_dictionary = []
    for s1 in symbols:
        all_in_dictionary.append(s1 in ADMITTED_ELEMENTS)
    return all(all_in_dictionary)


def check_connected_charged(smiles):
    return True
#    if "-" not in smiles and "." not in smiles and "+" not in smiles:
#        return True
#    else:
#        return False


def symbols2nuclear_charges(symbols):
    return np.array([NUCLEAR_CHARGE[at] for at in symbols])


def extract_smiles(nuc_q, coords, charge=0):
    nuc_q = [int(atom) for atom in nuc_q]

    smiles = Chem.RemoveHs(xyz2mol(nuc_q, coords, charge=charge)[0])
    return Chem.MolToSmiles(smiles)


def find_cnumber_keys(d):
    pattern = re.compile(r"c(\d+)")
    cnumber_keys = [key for key in d if pattern.match(key)]

    # Sort keys based on the numerical part
    cnumber_keys.sort(key=lambda x: int(pattern.match(x).group(1)))
    return cnumber_keys


def extract_EGP(all_egp):
    names = all_egp["EGP"].keys()
    SYMBOLS = []
    COORDS = []
    SMILES = []
    ENERGY = []
    ATOMIZATION = []
    SOLVATION = []
    DIPOLE = []
    X = []
    for name in names:
        try:
            # Todo: include all conformer information in the processing
            cnfs = find_cnumber_keys(all_egp["EGP"][name])
            symbols = all_egp["EGP"][name]["c0"]["Q"]
            nuc_q = symbols2nuclear_charges(symbols)
            coords = np.array(all_egp["EGP"][name]["c0"]["R"])
            dipole = [
                [all_egp["EGP"][name][cn]["dipole"][0] for cn in cnfs],
                [all_egp["EGP"][name][cn]["dipole"][1:] for cn in cnfs],
            ]

            charge = all_egp["EGP"][name]["c0"]["charge"]
            smiles = np.nan
            smiles = extract_smiles(nuc_q, coords, charge)

            check_charge = check_connected_charged(smiles)
            check_elements = check_if_in_dictionary(symbols)
            if check_elements and check_charge:
                CURR_SOLV = []
                for solv in solvent_names_array:
                    try:
                        value = all_egp["EGP"][name][solv]
#                        if value < 30 and value > -80:
                        CURR_SOLV.append(value)
#                        else:
#                            CURR_SOLV.append(np.nan)
                    except:
                        CURR_SOLV.append(np.nan)

                SOLVATION.append(CURR_SOLV)
                SMILES.append(smiles)
                ATOMIZATION.append([all_egp["EGP"][name][cn]["atomization"] for cn in cnfs])

                COORDS.append([all_egp["EGP"][name][cn]["R"] for cn in cnfs])
                ENERGY.append(all_egp["EGP"][name]["c0"]["energy"])
                SYMBOLS.append(symbols)
                DIPOLE.append(dipole)
                X.append(smiles_to_fingerprint(smiles))
        except:
            pass

    X, SYMBOLS, COORDS, SMILES, ATOMIZATION, ENERGY, SOLVATION, DIPOLE = (
        np.array(X),
        SYMBOLS,
        COORDS,
        SMILES,
        ATOMIZATION,
        np.array(ENERGY),
        np.array(SOLVATION),
        DIPOLE,
    )

    SOLV_DATA = {}
    for ind, name in enumerate(solvent_names_array):
        SOLV_DATA[name] = SOLVATION[:, ind]

    return (
        X,
        SYMBOLS,
        COORDS,
        SMILES,
        ATOMIZATION,
        ENERGY,
        SOLV_DATA,
        DIPOLE,
    )


def extract_GDB17(all_GDB17):
    names = all_GDB17["data"]["gdb17"].keys()
    SYMBOLS = []
    COORDS = []
    SMILES = []
    ENERGY = []
    ATOMIZATION = []
    SOLVATION = []
    DIPOLE = []
    X = []
    for name in names:
        try:
            cnfs = find_cnumber_keys(all_GDB17["data"]["gdb17"][name])
            symbols = all_GDB17["data"]["gdb17"][name]["c0"]["Q"]
            nuc_q = symbols2nuclear_charges(symbols)
            coords = np.array(all_GDB17["data"]["gdb17"][name]["c0"]["R"])

            dipole = [
                [all_GDB17["data"]["gdb17"][name][cn]["dipole"][0] for cn in cnfs],
                [all_GDB17["data"]["gdb17"][name][cn]["dipole"][1:] for cn in cnfs],
            ]

            charge = all_GDB17["data"]["gdb17"][name]["c0"]["charge"]

            smiles = np.nan
            smiles = extract_smiles(nuc_q, coords, charge)
            check_elements = check_if_in_dictionary(symbols)
            check_charge = check_connected_charged(smiles)

            if check_elements and check_charge:
                CURR_SOLV = []
                for solv in solvent_names_array:
                    try:
                        value = all_GDB17["data"]["gdb17"][name][solv]
#                        if value < 30 and value > -80:
                        CURR_SOLV.append(value)
#                        else:
#                            CURR_SOLV.append(np.nan)
                    except:
                        CURR_SOLV.append(np.nan)

                SOLVATION.append(CURR_SOLV)
                SMILES.append(smiles)
                ATOMIZATION.append(
                    [all_GDB17["data"]["gdb17"][name][cn]["atomization"] for cn in cnfs]
                )
                COORDS.append([all_GDB17["data"]["gdb17"][name][cn]["R"] for cn in cnfs])
                ENERGY.append(all_GDB17["data"]["gdb17"][name]["c0"]["energy"])
                SYMBOLS.append(symbols)
                DIPOLE.append(dipole)
                X.append(smiles_to_fingerprint(smiles))
        except:
            pass

    X, SYMBOLS, COORDS, SMILES, ATOMIZATION, ENERGY, SOLVATION, DIPOLE = (
        np.array(X),
        SYMBOLS,
        COORDS,
        SMILES,
        ATOMIZATION,
        np.array(ENERGY),
        np.array(SOLVATION),
        DIPOLE,
    )

    SOLV_DATA = {}
    for ind, name in enumerate(solvent_names_array):
        SOLV_DATA[name] = SOLVATION[:, ind]

    return (
        X,
        SYMBOLS,
        COORDS,
        SMILES,
        ATOMIZATION,
        ENERGY,
        SOLV_DATA,
        DIPOLE,
    )


def smiles_to_fingerprints(smiles_list, n_bits=512):
    fingerprints = []
    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
        fingerprints.append(fp)
    return fingerprints


def smiles_to_fingerprint(smiles, n_bits=512):
    mol = Chem.MolFromSmiles(smiles)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
    return fp


def plot_umap(fingerprints, properties):
    # Convert the RDKit explicit vectors to NumPy arrays
    fingerprint_arr = [list(fp) for fp in fingerprints]

    # Perform UMAP dimensionality reduction
    reducer = umap.UMAP(n_components=2)
    embedding = reducer.fit_transform(fingerprint_arr)

    # Create a scatter plot
    plt.scatter(embedding[:, 0], embedding[:, 1], c=properties, cmap="viridis")
    plt.colorbar()
    plt.title("Chemical Space Visualization using UMAP")
    plt.xlabel("UMAP Dimension 1")
    plt.ylabel("UMAP Dimension 2")
    plt.show()


def plot_incremental_pca(fingerprints, properties, n_components=2, batch_size=None):
    # Convert the RDKit explicit vectors to NumPy arrays
    fingerprint_arr = np.array([list(fp) for fp in fingerprints])

    # Perform Incremental PCA dimensionality reduction
    ipca = IncrementalPCA(n_components=n_components, batch_size=batch_size)
    reduced_data = ipca.fit_transform(fingerprint_arr)

    # Create a scatter plot
    plt.scatter(reduced_data[:, 0], reduced_data[:, 1], c=properties, cmap="viridis", s=5)
    plt.colorbar(label="Property Value")
    plt.title("Chemical Space Visualization using Incremental PCA")
    plt.xlabel("PCA Dimension 1")
    plt.ylabel("PCA Dimension 2")
    plt.show()


def combine_dictionaries(dict1, dict2):
    combined_dict = {}

    # Iterate over the first dictionary and concatenate or add the arrays
    for key, value in dict1.items():
        if key in dict2:
            combined_dict[key] = np.concatenate((value, dict2[key]))

    return combined_dict


def scatter_plot(
    X,
    Y,
    xlabel,
    ylabel,
    title,
    include_reg_line=True,
    marker_size=20,
    marker_color="blue",
):
    # Set plot style
    sns.set(style="whitegrid")

    # Create a figure and a set of subplots
    plt.close()
    plt.clf()
    fig, ax = plt.subplots()

    # Scatter plot with optional regression line
    sns.regplot(
        x=X,
        y=Y,
        ax=ax,
        scatter_kws={"s": marker_size, "color": marker_color},
        line_kws={"color": "red"},
        fit_reg=include_reg_line,
    )

    # Setting labels and title with increased font size
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14)

    # Despine
    sns.despine()

    plt.show()
    plt.close()


def histogram_plot(X, xlabel, title, kde=False, bins="fd"):
    # Set plot style
    sns.set(style="whitegrid")

    # Create a figure and a set of subplots
    plt.close()
    plt.clf()
    fig, ax = plt.subplots()

    # Calculate bins if necessary
    if bins == "fd":  # Freedman-Diaconis rule
        q1, q3 = np.percentile(X, [25, 75])
        bin_width = 2 * (q3 - q1) / len(X) ** (1 / 3)
        bins = int((X.max() - X.min()) / bin_width)

    # Plotting the histogram
    sns.histplot(X, ax=ax, kde=kde, bins=bins, edgecolor="black")

    # Setting labels and title with increased font size
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_title(title, fontsize=14)

    # Despine
    sns.despine()

    plt.show()
    plt.close()


def numpy_encoder(obj):
    """Special JSON encoder for numpy types"""
    if isinstance(
        obj,
        (
            np.int_,
            np.intc,
            np.intp,
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
        ),
    ):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    return json.JSONEncoder().default(obj)


def save_dict_to_json(d, filename):
    with open(filename, "w") as f:
        json.dump(d, f, default=numpy_encoder, indent=4)


def load_json_to_dict(filename, convert_to_numpy=False):
    with open(filename, "r") as f:
        d = json.load(f)

    if convert_to_numpy:

        def convert(item):
            if isinstance(item, list):
                return np.array(item)
            if isinstance(item, dict):
                return {key: convert(value) for key, value in item.items()}
            return item

        d = convert(d)

    return d


def find_duplicate_indices(lst):
    seen = {}
    duplicates = {}

    for index, element in enumerate(lst):
        if element in seen:
            if element in duplicates:
                duplicates[element].append(index)
            else:
                duplicates[element] = [seen[element], index]
        else:
            seen[element] = index

    return duplicates


def find_unique_indices(lst):
    seen = set()
    unique_indices = []

    for index, element in enumerate(lst):
        if element not in seen:
            unique_indices.append(index)
            seen.add(element)

    return unique_indices


def learning_curve(data_dict):
    import numpy as np
    import xgboost as xgb
    from sklearn.metrics import mean_absolute_error
    from sklearn.model_selection import train_test_split

    # Your data from the Pdb
    X = data_dict["ECFP"]  # Features
    y = data_dict["SOLVATION"]["h2o"]  # Target variable

    # Remove NaN values
    valid_indices = ~np.isnan(y)
    X = X[valid_indices]
    y = y[valid_indices]

    # Print the number of entries left without NaN
    print(f"Number of entries without NaN: {len(y)}")

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize XGBoost regressor
    model = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=500,
        learning_rate=0.01,
        max_depth=6,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.01,
        reg_lambda=1,
        gamma=0.1,
    )

    # Learning curve: Train model on increasing sizes of the training set
    N_train_vec = [2**i for i in range(int(np.log2(len(X_train))) + 1)]
    N_train_vec.append(len(X_train))
    for n in N_train_vec:
        # Train the model
        model.fit(X_train[:n], y_train[:n])

        # Make predictions and compute MAE on the test set
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)

        # Print N_train and MAE
        print(f"N_train: {n}, MAE on Test Set: {mae}")

# qml2 taken from: https://github.com/qml2code/qml2
# competent_formatting taken from: https://github.com/kvkarandashev/competent_formatting
import json, os
import numpy as np
import matplotlib.pyplot as plt
from qml2.dataset_formats.qm9 import read_SMILES, xyz_SMILES_consistent
from competent_formatting.tables import latex_table
from competent_formatting.SMILES import latex_SMILES


folder = os.environ["DATA"] + "/QM9IPEA"

au2eV = 27.211598535

name = folder + "/QM9IPEA.json"

print("CHECKING:", name)


with open(name, "r") as f:
    data_dict = json.load(f)

method = "PNO-LCCSD(T*)-F12B"
quant_orb = "LUMO_ENERGY"
quant_en = "ELECTRON_AFFINITY"

x_separator = [-0.5, 1.0]
y_separator = [1.75, 0.0]

line = np.polyfit(x_separator, y_separator, 1)
p = np.poly1d(line)


def SMILES_wvalidity(QM9_id):
    QM9_xyz = os.environ["DATA"] + "/QM9_formatted/dsgdb9nsd_%06d.xyz" % QM9_id
    SMILES = read_SMILES(QM9_xyz)
    SMILES_valid = xyz_SMILES_consistent(QM9_xyz)
    return SMILES, SMILES_valid, QM9_xyz


def get_latex_columns(latex_info):
    id_column = ["id"]
    SMILES_column = ["SMILES"]
    for QM9_id, SMILES, SMILES_valid in latex_info:
        id_column.append(QM9_id)
        SMILES_str = latex_SMILES(SMILES)
        if not SMILES_valid:
            SMILES_str = SMILES_str + r"$\dagger$"
        SMILES_column.append(SMILES_str)
    return [id_column, SMILES_column]


def print_latex_table(latex_info):
    latex_info.sort()
    half_number = len(latex_info) // 2

    #    transposed_table=get_latex_columns(latex_info[:half_number])+[[phantom for _ in range(half_number+1)]]+get_latex_columns(latex_info[half_number:])
    transposed_table = get_latex_columns(latex_info[:half_number]) + get_latex_columns(
        latex_info[half_number:]
    )

    latex_output = latex_table(
        transposed_table, column_types="ll|ll", transposed=True, midrule_positions=[1]
    )
    open("QM9IPEA_weird_LUMO.tex", "w").write(latex_output)


def plot_corr():
    x = []
    y = []

    x1 = []
    y1 = []

    latex_info = []

    printed_tuples = []
    for val1_unscaled, val2_unscaled, QM9_id in zip(
        data_dict[quant_orb], data_dict[quant_en][method], data_dict["QM9_ID"]
    ):
        if np.isnan(val1_unscaled) or np.isnan(val2_unscaled):
            continue
        val1 = val1_unscaled * au2eV
        val2 = val2_unscaled * au2eV
        if p(val1) < val2:
            x.append(val1)
            y.append(val2)
            SMILES, SMILES_valid, QM9_xyz = SMILES_wvalidity(QM9_id)
            printed_tuples.append((val1, val2, SMILES, SMILES_valid, QM9_xyz, QM9_id))
            latex_info.append((QM9_id, SMILES, SMILES_valid))
        else:
            x1.append(val1)
            y1.append(val2)
    # calc the trendline (it is simply a linear fitting)
    plt.plot(x, y, "x", color="blue")
    plt.plot(x1, y1, "+", color="red")
    plt.plot(x_separator, p(x_separator), "-", color="green")
    # the line equation:
    plt.xlabel(quant_orb)
    plt.ylabel(quant_en)
    plt.title(method)
    plt.show()
    plt.clf()
    with open(f"quant_cut_{method}.txt", "w") as f:
        for t in printed_tuples:
            print(*t, file=f)
    print_latex_table(latex_info)


plot_corr()

# competent_formatting taken from: https://github.com/kvkarandashev/competent_formatting
import os, json
import numpy as np
from sklearn.metrics import r2_score
from competent_formatting.tables import (
    latex_table,
    MultiColumn,
    MultiRow,
    LaTeXPlainFloat,
)
from competent_formatting.number_formatting.utils import pminus
from sortedcontainers import SortedList
from sklearn import linear_model

ntable_numerals=2

latex_float_formatter=LaTeXPlainFloat(ntable_numerals)

float_format_str=latex_float_formatter.init_format_string

method_label_dict = {
    "DFHF": "DF-HF",
    "DFHF+CABS": "DF-HF-CABS",
    "PNO-LCCSD-F12B": "PNO-LCCSD-F12b",
    "PNO-LCCSD(T)-F12B": "PNO-LCCSD(T)-F12b",
    "PNO-LCCSD(T*)-F12B": "PNO-LCCSD(T*)-F12b",
}

def get_method_label(method):
    if method in method_label_dict:
        return method_label_dict[method]
    else:
        return method

folder = os.environ["DATA"] + "/QM9IPEA"

name = folder + "/QM9IPEA.json"

print("CHECKING:", name)

with open(name, "r") as f:
    data_dict = json.load(f)

atom_en="ATOMIZATION_ENERGY"

quantity_labels=[atom_en, "IONIZATION_ENERGY", "ELECTRON_AFFINITY"]

def filter_vals(xs, ys):
    filtered_xs=[]
    filtered_ys=[]
    for x, y in zip(xs, ys):
        if np.isnan(x) or np.isnan(y):
            continue
        filtered_xs.append(x)
        filtered_ys.append(y)
    return filtered_xs, filtered_ys

def calc_fit(xs, ys):
    filtered_xs, filtered_ys=filter_vals(xs, ys)

    z = np.polyfit(filtered_xs, filtered_ys, 1)
    p = np.poly1d(z)
    R_val = r2_score(filtered_ys, p(filtered_xs))
    return (*z, R_val)

def formula_str(slope, intercept):
#    intercept_str=float_format_str.format(intercept)
    intercept_str=latex_float_formatter.get_formatted_float(intercept, minus=True)
#    if intercept > 0.:
#        intercept_str="+"+intercept_str
#    return "y="+float_format_str.format(slope)+"x"+intercept_str
    return float_format_str.format(slope)+","+intercept_str

def print_table(quant_dict, quant_label):
    methods=list(quant_dict.keys())
    R_row1=[MultiRow("fitted method",2), MultiColumn("linear fit's $R^{2}$ score", len(methods))]
    method_row=[None]+["\\rotatebox[origin=c]{75}{"+get_method_label(method)+"}" for method in methods]
    R_table=[R_row1, method_row]

    formula_row1=[MultiRow("fitted method",2), MultiColumn("linear fit's slope and intercept", len(methods))]
    formula_table=[formula_row1, method_row]
    for fitted_method in methods:
        ys=quant_dict[fitted_method]
        new_R_row=[get_method_label(fitted_method)]
        new_formula_row=[get_method_label(fitted_method)]
        for x_method in methods:
            if fitted_method == x_method:
                new_R_row.append(1.0)
                new_formula_row.append(float_format_str.format(1.)+",$"+pminus+"$"+float_format_str.format(0.))
                continue
            xs=quant_dict[x_method]
            slope, intercept, R2=calc_fit(xs, ys)
            new_R_row.append(R2)
            new_formula_row.append(formula_str(slope, intercept))
        R_table.append(new_R_row)
        formula_table.append(new_formula_row)
    R_latex_output = latex_table(
        R_table,
        midrule_positions=[
            2,
        ],
        float_formatter=latex_float_formatter,
        column_types="l"+"c"*len(methods),
        cline_positions={1 : [(2, len(methods)+1)]}
    )
    formula_latex_output = latex_table(
        formula_table,
        midrule_positions=[
            2,
        ],
        float_formatter=latex_float_formatter,
        column_types="l"+"c"*len(methods),
        cline_positions={1 : [(2, len(methods)+1)]}
    )
    open("QM9IPEA_correlations_R2_" + quant_label + ".tex", "w").write(R_latex_output)
    open("QM9IPEA_correlations_formulas_" + quant_label + ".tex", "w").write(formula_latex_output)

for quant_label in quantity_labels:
    quant_dict=data_dict[quant_label]
    print_table(quant_dict, quant_label)

print_table(data_dict["ENERGY"]["0"], "GROUND_ENERGY")

# lastly, print R2 for fitting atomizating energy as sum of atomic contributions.
all_symbols=data_dict["SYMBOLS"]

def atomization_energy_fitting_row(method):
    all_available_symbols=SortedList()
    values=data_dict[atom_en][method]
    filtered_values=[]
    filtered_elements=[]
    for val, els in zip(values, all_symbols):
        if np.isnan(val):
            continue
        filtered_values.append(val)
        filtered_elements.append(els)
        for el in els:
            if el not in all_available_symbols:
                all_available_symbols.add(el)
    nmols=len(filtered_elements)
    nels=len(all_available_symbols)
    fit_coeffs=np.zeros((nmols, nels))
    for mol_id, els in enumerate(filtered_elements):
        for el in els:
            fit_coeffs[mol_id, all_available_symbols.index(el)]+=1.

    clf = linear_model.LinearRegression(fit_intercept=True)
    clf.fit(fit_coeffs, filtered_values)
    print("Prop coeffs:", method)
    for el, coeff in zip(all_available_symbols, clf.coef_):
        print(el, coeff)
    print("intercept:", clf.intercept_)
#    R_val = r2_score(filtered_values, p(fit_coeffs))
    return clf.score(fit_coeffs, filtered_values)

methods=list(data_dict["ENERGY"]["0"].keys())
for method in methods:
    print(atomization_energy_fitting_row(method))

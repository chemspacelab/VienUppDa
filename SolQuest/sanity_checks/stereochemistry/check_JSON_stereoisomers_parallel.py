import numpy as np
import sys
import os
from check_JSON_stereoisomers import (
    stereoisomer_smiles_list,
    RDKitFailure,
    filter_wsame_nitrogen,
    are_tautomers,
    only_one_reasonable,
    get_all_SMILES,
    print_wlen,
)
from joblib import Parallel, delayed

valid_lbl = 0
rdkit_failure_lbl = 1
stereotautomer_lbl = 2
stereoactive_nitrogen_lbl = 3
unreasonable_excluded_lbl = 4
invalid_lbl = 5


def all_stereochecks(SMILES, energy):
    if np.isnan(energy):
        return valid_lbl
    try:
        isomers = stereoisomer_smiles_list(SMILES)
    except RDKitFailure:
        return rdkit_failure_lbl
    if len(isomers) == 1:
        return valid_lbl
    new_isomers = filter_wsame_nitrogen(isomers)
    if len(new_isomers) == 1:
        return stereoactive_nitrogen_lbl
    # check if discrepancy is due to tautomers
    if are_tautomers(new_isomers):
        return stereotautomer_lbl
    # check if all other isomers are unreasonable
    if only_one_reasonable(new_isomers):
        return unreasonable_excluded_lbl
    return invalid_lbl


def stereochecks_parallel(all_SMILES, all_energies):
    nprocs = int(os.environ["OMP_NUM_THREADS"])
    return Parallel(n_jobs=nprocs)(
        delayed(all_stereochecks)(SMILES, energy) for SMILES, energy in zip(all_SMILES, all_energies)
    )


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

    appended_dict = {
        rdkit_failure_lbl: rdkit_failures,
        invalid_lbl: badly_defined_SMILES,
        stereoactive_nitrogen_lbl: stereoactive_nitrogen_SMILES,
        stereotautomer_lbl: stereotautomer_SMILES,
        unreasonable_excluded_lbl: unreasonable_excluded_SMILES,
    }

    SMILES_labels = stereochecks_parallel(all_SMILES, all_energies)

    for SMILES, SMILES_label in zip(all_SMILES, SMILES_labels):
        if SMILES_label == valid_lbl:
            continue
        assert SMILES_label in appended_dict
        appended_dict[SMILES_label].append(SMILES)

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

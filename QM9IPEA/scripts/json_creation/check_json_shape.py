# Quickly check JSON's shape makes sense.
import json
import math
import sys

import numpy as np

np.random.seed(1)

name = sys.argv[1]

print("CHECKING:", name)

with open(sys.argv[1], "r") as f:
    data_dict = json.load(f)


def print_indented_str(s, indent=0):
    print(" " * indent + s)


def num_valid_entries(l):
    num = 0
    for entry in l:
        if isinstance(entry, np.ndarray) or isinstance(entry, list) or isinstance(entry, str):
            isnan = False
        else:
            isnan = math.isnan(entry)
        if not isnan:
            num += 1
    return num


def print_structure(d_in, indent=0):
    for k, entry in d_in.items():
        if isinstance(entry, dict):
            print_indented_str(k + " :", indent=indent)
            print_structure(entry, indent=indent + 1)
        else:
            print_indented_str(
                k + " : " + str(len(entry)) + "," + str(num_valid_entries(entry)),
                indent=indent,
            )


print_structure(data_dict)

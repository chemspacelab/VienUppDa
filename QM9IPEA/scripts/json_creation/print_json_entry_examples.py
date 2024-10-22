import json
import sys

import numpy as np

np.random.seed(2)

example_ids = [np.random.randint(7000) for _ in range(5)]

with open(sys.argv[1], "r") as f:
    data_dict = json.load(f)


def attempt_print_examples(entry):
    if isinstance(entry, list):
        for i in example_ids:
            print(i, ";", entry[i])
    else:
        for k, subentry in entry.items():
            print(k, ":")
            attempt_print_examples(subentry)


attempt_print_examples(data_dict)

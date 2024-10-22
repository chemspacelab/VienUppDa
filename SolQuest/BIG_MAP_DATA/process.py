import json
import os
import pickle


def combine_dictionaries(ALL_GDB17):
    COMBINED = {"data": {"gdb17": {}}}

    # Assuming ALL_GDB17 is a list of dictionaries with the same structure
    for gdb_dict in ALL_GDB17:
        # Loop through each key-value pair in the "gdb17" dictionary
        for key, value in gdb_dict["gdb17"].items():
            # Add the key-value pair to the combined dictionary only if the key is not already present
            if key not in COMBINED["data"]["gdb17"]:
                COMBINED["data"]["gdb17"][key] = value
    return COMBINED


def get_gdb_names(GDB_17_PATH):
    GDB17_DONE = []

    for root, dirs, files in os.walk(GDB_17_PATH):
        for file in files:
            if "_DONE_" in file:
                GDB17_DONE.append(file)
    return GDB17_DONE


def load_data(path):
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data


# save dict as JSON file
def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    AMONS_GDB17_PATH = "./dataset_processed/AMONS/GDB17/"
    AMONS_ZINC_PATH = "./dataset_processed/AMONS/ZINC/"

    GDB_17_PATH = "./dataset_processed/GDB17/"
    EGP_PATH = "./dataset_processed/EGP/"

    ALL_EGP = []
    for ind, done_file in enumerate(os.listdir(EGP_PATH)):
        EGP_data = load_data(EGP_PATH + done_file)
        ALL_EGP.append(EGP_data)

    save_json(ALL_EGP[0], "egp_1.json")
    save_json(ALL_EGP[1], "egp_2.json")

    # list all files with _DONE_ pattern in the GDB subfolder
    GDB17_DONE = get_gdb_names(GDB_17_PATH)

    ALL_GDB17_1 = []
    for ind, done_file in enumerate(GDB17_DONE[:35]):
        GDB17_data = load_data(GDB_17_PATH + done_file)
        num_entries = len(GDB17_data["gdb17"].keys())
        ALL_GDB17_1.append(GDB17_data)

    ALL_GDB17_1 = combine_dictionaries(ALL_GDB17_1)
    save_json(ALL_GDB17_1, "all_gdb17_1.json")
    del ALL_GDB17_1

    ALL_GDB17_2 = []
    for ind, done_file in enumerate(GDB17_DONE[35:]):
        GDB17_data = load_data(GDB_17_PATH + done_file)
        num_entries = len(GDB17_data["gdb17"].keys())
        ALL_GDB17_2.append(GDB17_data)

    ALL_GDB17_2 = combine_dictionaries(ALL_GDB17_2)
    save_json(ALL_GDB17_2, "all_gdb17_2.json")
    del ALL_GDB17_2

    ALL_AMONS_GDB17 = {}
    for i in range(1, 8):
        if i < 7:
            amon_data = load_data(AMONS_GDB17_PATH + "amons_GDB17_ni{}.pkl".format(i))
            ALL_AMONS_GDB17["ni{}".format(i)] = {
                "data": amon_data,
                "raw_file": "amons_GDB17_ni{}.pkl".format(i),
            }
        else:
            for j in range(1, 4):
                amon_data = load_data(
                    AMONS_GDB17_PATH + "amons_GDB17_ni{}_part-{}.pkl".format(i, j)
                )
                ALL_AMONS_GDB17["ni{}_{}".format(i, j)] = {
                    "data": amon_data,
                    "raw_file": "amons_GDB17_ni{}_part-{}.pkl".format(i, j),
                }

    save_json(ALL_AMONS_GDB17, "all_amons_gdb17.json")

    ALL_AMONS_ZINC = {}
    for i in range(2, 8):
        if i < 6:
            amon_data = load_data(AMONS_ZINC_PATH + "amons_ZINC_ni{}.pkl".format(i))
            ALL_AMONS_ZINC["ni{}".format(i)] = {
                "data": amon_data,
                "raw_file": "amons_ZINC_ni{}.pkl".format(i),
            }
        else:
            for j in range(1, 6):
                try:
                    amon_data = load_data(
                        AMONS_ZINC_PATH + "amons_ZINC_ni{}_part-{}.pkl".format(i, j)
                    )
                    ALL_AMONS_ZINC["ni{}_{}".format(i, j)] = {
                        "data": amon_data,
                        "raw_file": "amons_ZINC_ni{}_part-{}.pkl".format(i, j),
                    }
                except:
                    print("ni{}_{} does not exist".format(i, j))

    save_json(ALL_AMONS_ZINC, "all_amons_zinc.json")

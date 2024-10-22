# KK: TBH I don't remember why I have this.
import os
from glob import glob


def name_nopath(f):
    return f.split("/")[-1]


def generate_xyz_dir_list(dir_in):
    if not os.path.isdir(dir_in):
        raise Exception
    output = [name_nopath(d) for d in glob(dir_in + "/*_xyz")]
    return sorted(output)


def xyz_files_to_dir(dir_in):
    if not os.path.isdir(dir_in):
        raise Exception
    output = ["_".join(name_nopath(f).split(".")) for f in glob(dir_in + "/*.xyz")]
    return sorted(output)


def find_contained_number(list1, list2):
    nmatch = 0
    for el1 in list1:
        if el1 in list2:
            nmatch += 1
    return nmatch


def generate_completed_xyz_dir_list(dir_in):
    l = generate_xyz_dir_list(dir_in)
    l_filtered = []
    for el in l:
        true_dir = dir_in + "/" + el
        if (len(glob(true_dir + "/*.inp")) != 0) or (os.path.isdir(true_dir + "/" + el)):
            l_filtered.append(el)
    return l_filtered


def generate_incomplete_xyz_dir_list(dir_in):
    l = generate_xyz_dir_list(dir_in)
    l_filtered = []
    for el in l:
        true_dir = dir_in + "/" + el
        if not ((len(glob(true_dir + "/*.inp")) != 0) or (os.path.isdir(true_dir + "/" + el))):
            l_filtered.append(el)
    return l_filtered

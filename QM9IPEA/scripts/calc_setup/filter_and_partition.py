import sys

from redox_database_gen.database_partitioning import random_tar_partition_xyz_list
from redox_database_gen.utils import dirs_xyz_list, rdkit_reasonable_molecules


def write_as_column(filename, list_in):
    f = open(filename, "w")
    for el in list_in:
        print(el, file=f)
    f.close()


def get_dir_name(full_dir_path):
    split_str = full_dir_path.split("/")
    for component in reversed(split_str):
        if component != "":
            return component
    return None


original_dataset_xyz_dir = sys.argv[1]

try:
    partition_size = int(sys.argv[2])
except IndexError:
    partition_size = 2000
partitioned_dataset_name = "partitioned_" + get_dir_name(original_dataset_xyz_dir)

original_xyz_list = dirs_xyz_list(original_dataset_xyz_dir)

filtered_list, rejected_list = rdkit_reasonable_molecules(original_xyz_list)

random_tar_partition_xyz_list(partitioned_dataset_name, filtered_list, partition_size)

write_as_column(partitioned_dataset_name + "/filtered_list.txt", filtered_list)

write_as_column(partitioned_dataset_name + "/rejected_list.txt", rejected_list)

# Create a tar file from a list of xyzs
def tar_from_xyz_list(tar_name, xyz_list, compression=None):
    import tarfile

    if compression is None:
        file_ending = ".tar"
        write_type = "x"
    else:
        file_ending = ".tar." + compression
        write_type = "x:" + compression
    new_tar = tarfile.open(tar_name + file_ending, write_type)
    for xyz_file in xyz_list:
        new_tar.add(xyz_file, arcname=xyz_file.split("/")[-1])
    new_tar.close()


# Several tar files from several lists of xyzs.
def tars_from_xyz_lists(partition_name, xyz_lists):
    import subprocess

    from joblib import Parallel, delayed

    from .utils import num_omp_procs

    subprocess.run(["mkdir", "-p", partition_name])
    tar_name_root = "./" + partition_name + "/" + partition_name + "_"
    Parallel(n_jobs=num_omp_procs(), backend="multiprocessing")(
        delayed(tar_from_xyz_list)(tar_name_root + str(list_id), xyz_list)
        for list_id, xyz_list in enumerate(xyz_lists)
    )


# Randomly partition a list of xyzs into "packages".
def random_partition_xyz_list(xyz_list, partition_size, seed=1):
    import copy
    import random

    created_xyz_list = copy.deepcopy(xyz_list)
    random.seed(seed)
    random.shuffle(created_xyz_list)
    partition_xyz_lists = []
    num_xyzs = len(xyz_list)
    lower_bound = 0
    upper_bound = partition_size
    while lower_bound < num_xyzs:
        partition_xyz_lists.append(created_xyz_list[lower_bound:upper_bound])
        lower_bound = upper_bound
        upper_bound = min(upper_bound + partition_size, num_xyzs)
    return partition_xyz_lists


def random_tar_partition_xyz_list(partition_name, *args, **kwargs):
    partitioned_list = random_partition_xyz_list(*args, **kwargs)
    tars_from_xyz_lists(partition_name, partitioned_list)

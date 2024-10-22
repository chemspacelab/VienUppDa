from redox_database_gen.database_partitioning import random_tar_partition_xyz_list
from redox_database_gen.utils import dirs_xyz_list

test_xyzs = dirs_xyz_list("../../tests/qm7_sample_mols")
random_tar_partition_xyz_list("partitioned_qm7_xyzs", test_xyzs, 5)

# Copy all files from atom_ens to a directory with a structure more suitable for NOMAD upload.
import os
import subprocess

# Directory where initial calculations are kept.
init_dir = "atom_ens"

new_dir = "atom_ens_upload"
# file types that should be copied
good_endings = ["inp", "out", "xml"]


init_dir_full = os.getcwd() + "/" + init_dir
new_dir_full = os.getcwd() + "/" + new_dir


def run(*args):
    subprocess.run(list(args))


def file_ending(file_str):
    return file_str.split(".")[-1]


def check_dir(master_dir, upload_name):
    os.chdir(master_dir)
    for subdir in os.listdir():
        if os.path.isdir(subdir):
            check_dir(subdir, upload_name)
            continue
        fend = file_ending(subdir)
        if fend not in good_endings:
            continue
        new_filename = new_dir_full + "/" + upload_name + "/" + upload_name + "." + fend
        run("cp", subdir, new_filename)
    os.chdir("..")


os.chdir(init_dir_full)
for subdir in os.listdir():
    el = subdir
    upload_name = el + "_atom_en"
    run("mkdir", "-p", new_dir_full + "/" + upload_name)
    check_dir(subdir, upload_name)

    os.chdir(init_dir_full)

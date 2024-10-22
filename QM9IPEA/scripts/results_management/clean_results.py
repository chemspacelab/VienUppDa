import os
from subprocess import run

cleaned_dir = "results_cleaned"

bad_endings = [
    "xyz",
    "sh",
    "stderr",
    "stdout",
    "timestamps",
    "com",
    "cpu_mem_logs",
    "py",
    "bucket",
    "job",
    "tgz",
    "txt",
]


def to_delete(subdir):
    if subdir in ["scratch", "FINISHED"]:
        return True
    if not os.path.isfile(subdir):
        return
    spl = subdir.split(".")
    if (len(spl) > 1) and (spl[-1] in bad_endings):
        return True
    if (len(spl) > 2) and (spl[-1] == "failed" and spl[-2] == "wfu"):
        return True
    return False


def rm(f):
    run(["rm", "-Rf", f])


up = ".."


def check_directory(d, lvl=0):
    os.chdir(d)
    for subdir in os.listdir():
        if to_delete(subdir):
            rm(subdir)
            continue
        if not os.path.isfile(subdir):
            check_directory(subdir, lvl=lvl + 1)
            if lvl != 0:
                rm(subdir)
            continue
    if lvl > 1:
        for subdir in os.listdir():
            run(["mv", subdir, up])
    os.chdir(up)


check_directory(cleaned_dir)

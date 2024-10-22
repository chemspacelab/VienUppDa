# VienUppDa

Scripts used during the collaboration between University of **Vien**na and University of **Upp**sala on generating accurate reference **da**ta for machine learning algorithm testing and validation. The computational protocol is outlined in the [corresponding manuscript](https://arxiv.org/XXXXX) with the resulting data uploaded to [Zenodo](https://zenodo.org/records/11036086).

# Repository structure

## SolQuest

Contains folders with free energies of solvation in various solvents

- `cosmo_scripts` - scripts for processing raw cosmo files. Requires installation of `cosmotherm` script. Ensures the right input file `cosmo.inp` is passed to `cosmotherm`. Then launches the postprocessing calculations in parallel using all available cores and for an array of user defined temperatures.
- `BIG_MAP_DATA` - scripts used to process solvation energy data including geometries into JSON files


## QM9IPEA

Contains folders:

-`redox_database_gen` - Python module used to manage MOLPRO calculations and, before the launch of `leruli.com` queueing system, to control execution of those calculations on different machines.
- `templates` - templates of MOLPRO scripts used by `redox_database_gen` to run calculations.
- `examples` - scripts verifying `redox_database_gen` is working correctly.
- `scripts` - additional scripts used to launch calculations (`calc_setup`), collect and curate the results (`results_management`), interact with `leruli.com` (`leruli`), create Docker files for the calculation (`docker_creation`), and create the final JSON files (`json_creation`)

#!/bin/bash
# Check the image created in ../compose actually works.

cp ../../../templates/molpro_redox_calc/molpro_redox.com .

docker run -v "$(pwd):/rundir" bigmap_redox_calc:1.0 python full_calc_script.py h2.xyz

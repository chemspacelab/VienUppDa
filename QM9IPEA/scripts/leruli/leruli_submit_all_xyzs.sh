#!/bin/bash

scrdir=$(echo $0 | rev | cut -d '/' -f 2- | rev)

xyz_dir=$1

if [ "$xyz_dir" == "" ]
then
    echo "Specify xyz directory."
    exit
fi

pyscript=full_calc_launch.py

cp $scrdir/$pyscript $xyz_dir

cp $scrdir/../../templates/molpro_redox_calc/molpro_redox.com $xyz_dir

cd $xyz_dir

for xyz in $(ls *.xyz | shuf | tr '\n' ' ')
do
    dirname=$(echo $xyz | tr '.' '_')
    if [ ! -d $dirname ]
    then
        mkdir $dirname
        cd $dirname
        cp ../$xyz .
        cp ../$pyscript .
        cp ../molpro_redox.com .
        leruli task-submit --cores 23 --memory 100000 bigmap_redox_calc 1.1 "python $pyscript $xyz"
        cd ..
    fi
done

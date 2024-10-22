#!/bin/bash

if [ "$1" == "" ]
then
    echo "Choose a directory to process."
    exit
fi

MYDIR=$(pwd)

for i in $1/*_xyz
do
    if [ -f $i/"FINISHED" ]
    then
        xyz_name=$(echo $i | rev | cut -d'_' -f2- | rev).xyz
        echo "COMPLETED: $xyz_name"
        rm -f $xyz_name
    fi
done

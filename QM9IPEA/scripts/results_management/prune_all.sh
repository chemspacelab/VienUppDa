#!/bin/bash

if [ "$1" == "" ]
then
    echo "Choose a directory to process".
    exit
fi

MYDIR=$(pwd)

for i in $1/*_xyz
do
    cd $i
    leruli task-prune #$(cat leruli.bucket)
    cd $MYDIR
done

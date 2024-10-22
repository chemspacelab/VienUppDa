#!/bin/bash

if [ "$1" == "" ]
then
    echo "Choose a directoty to process".
    exit
fi

MYDIR=$(pwd)

for i in $1/*_xyz
do
    stat=$(leruli task-status $(cat $i/leruli.job))
    if [ "$stat" == "completed" ] || [ "$stat" == "canceled" ]
    then
        echo "Recovering $i"
        cd $i
        leruli task-get $(cat leruli.bucket)
        cd $MYDIR
    fi
done

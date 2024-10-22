#!/bin/bash

if [ "$1" == "" ]
then
    echo "Choose a directory to process."
    exit
fi

MYDIR=$(pwd)

for i in $1/*_xyz
do
    stat=$(leruli task-status $(cat $i/leruli.job))
    REMOVE=FALSE
    if [ "$stat" == "completed" ] || [ "$stat" == "canceled" ] || [ "$stat" == "No such job or not your job." ] || [ "$stat" == "submitted" ]
    then
        if [ ! -f $i/"FINISHED" ]
        then
            REMOVE=TRUE
        fi
    fi
    if [ "$stat" == "failed: Input files missing" ]
    then
        REMOVE=TRUE
    fi
    if [ "$REMOVE" == "TRUE" ]
    then
        echo "REMOVING: $i"
        rm -Rf $i
    fi
done

#!/bin/bash

if [ "$1" == "" ]
then
    echo "Choose a directoty to process".
    exit
fi

for i in $1/*/leruli.job
do
    echo $i
    jobid=$(cat $i)
    s=$(leruli task-status $jobid)
    echo $s
    if [ "$s" != "running" ] && [ "$s" != "completed" ]
    then
        echo "Cancelling"
        leruli task-cancel $jobid
    fi
done

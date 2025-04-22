#!/bin/bash
# K.Karan: NOTE: while I used the script to check that SMILES in the *.json's are stereochemically well-defined, the final steps of the process involved using Morfeus-ML + VMD to manually look at 99 SMILES that the algorithm (unjustly) flagged as ill-defined.

d=$DATA/SolQuest

for i in $d/*.zip $d/*.json
do
    echo $i
    python check_JSON_stereoisomers_parallel.py $i $(basename $i)
done

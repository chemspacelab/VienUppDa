
for i in {2..5..1}
do
	path=/data/jan/calculations/database/AMONS/ZINC/Results_of_BP-TZVPD-FINE-COSMO/ni${i}
        python run_frngs_solvents.py -PATH ${path} -OUT AMONS_ZINC_ni${i} -mode txt -Tl 25 -Th 30 -name amonsZINC
done


path=/data/jan/calculations/database/AMONS/ZINC/Results_of_BP-TZVPD-FINE-COSMO/ni6/part-
for i in {1..2..1}
do
        python run_frngs_solvents.py -PATH ${path}$i -OUT AMONS_ZINC_ni6_part-${i} -mode txt -Tl 25 -Th 30 -name amonsZINC
done





path=/data/jan/calculations/database/AMONS/ZINC/Results_of_BP-TZVPD-FINE-COSMO/ni7/part-
for i in {1..5..1}
do
        python run_frngs_solvents.py -PATH ${path}$i -OUT AMONS_ZINC_ni7_part-${i} -mode txt -Tl 25 -Th 30 -name amonsZINC
done



exit








exit

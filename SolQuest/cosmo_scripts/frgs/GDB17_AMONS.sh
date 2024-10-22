path=/data/jan/calculations/database/AMONS/GDB17/Results_of_BP-TZVPD-FINE-COSMO/ni7/part-
for i in {1..3..1}
do
        python run_frngs.py -PATH ${path}$i -OUT AMONS_GDB17_ni7_part-${i} -mode txt -Tl 25 -Th 30 -name amonsGDB
done

for i in {1..6..1}
do
        path=/data/jan/calculations/database/AMONS/GDB17/Results_of_BP-TZVPD-FINE-COSMO/ni${i}
        python run_frngs.py -PATH ${path} -OUT AMONS_GDB17_ni${i} -mode txt -Tl 25 -Th 30 -name amonsGDB
done

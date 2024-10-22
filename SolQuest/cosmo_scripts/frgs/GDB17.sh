#get current directory
source /home/jan/miniconda3/bin/activate

cwd=$(pwd)
packed_path=/data/jan/calculations/database/GDB17/vsc/packed/processing
unpack_path=/data/jan/calculations/database/GDB17/vsc/unpacked_curr
GEOPATH=/data/jan/calculations/database/GDB17/vsc/geos
#list all tar gz files in the directory packed_path
#cp them to the unpacked directory and unpack them
for i in $(ls ${packed_path}/*.tar.gz)
do
        cp $i ${unpack_path}
        echo $i

        file_name=$(basename $i)
        echo ${unpack_path}/${file_name}
        tar -xf ${unpack_path}/${file_name} -C ${unpack_path}
        file_name=${file_name%.*}

        file_name_no_tar=${file_name%.*}
        echo $file_name_no_tar

        for mol in $(ls ${unpack_path}/${file_name_no_tar})
        do
            echo ${unpack_path}/${file_name_no_tar}/$mol/Results_of_BP-TZVPD-FINE-COSMO/

            mv ${unpack_path}/${file_name_no_tar}/$mol/Results_of_BP-TZVPD-FINE-COSMO/* ${unpack_path}/work
            echo $cwd
            #exit
        done


        python run_frngs_solvents.py -PATH ${unpack_path}/work -OUT GDB17_${file_name_no_tar} -mode txt -Tl 25 -Th 30 -name gdb17
        python /home/jan/projects/FML/cosmodata/cosmo_scripts/geometries/process.py -SAVE_PATH ${GEOPATH} -PATH ${unpack_path}/work -name_tag gdb17 -tarname ${file_name_no_tar}

        rm ${unpack_path}/${file_name}.gz
        #instead of removing the files with a * use a loop to remove the files
        for j in $(ls ${unpack_path}/work)
        do
            rm ${unpack_path}/work/$j
        done
        rm -rf ${unpack_path}/${file_name_no_tar}
done

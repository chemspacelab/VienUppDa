#!/bin/bash

rm -Rf molpro_2021.1
rm -Rf redox_database_gen

cp -rf ../molpro_2021.1 .
cp -rf ../../../redox_database_gen .

cat > Dockerfile << EOF
FROM continuumio/miniconda3:4.10.3-alpine as build
COPY molpro_2021.1 /usr/local/molpro/molpro_2021.1
COPY redox_database_gen /extra_modules/redox_database_gen
ENV PATH /usr/local/molpro/molpro_2021.1/bin:\$PATH
ENV PYTHONPATH /extra_modules:\$PYTHONPATH
SHELL ["/bin/bash", "--login", "-c"]
VOLUME "/rundir"
WORKDIR "/rundir"
EOF

#docker image build .
docker image build -t bigmap_redox_calc:1.0 .

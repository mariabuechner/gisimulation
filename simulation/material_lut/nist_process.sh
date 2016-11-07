#!/bin/bash

echo "Copy ascii data from http://physics.nist.gov/PhysRefData/XrayMassCoef/ElemTab/z79.html and save it to Au_nist.nist, then run this script with the nist file as argument to generate an Au_nist.dat file without the headers"

for f in $*; do
  OUT=$(basename "$f" nist)dat
  sed 's#..##' < "$f" | awk '/E/{ print $1, $2 }' > "$OUT"
done

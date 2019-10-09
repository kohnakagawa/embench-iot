#!/bin/sh

for i in "matmult-int" "nbody" "st" "aha-mont64" "crc32" "minver" "cubic" "nettle-aes"
do
    ./bd/src/$i/$i
done

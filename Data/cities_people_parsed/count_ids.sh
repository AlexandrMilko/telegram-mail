#!/bin/bash
i=0
for id in $(cat +*.txt)
do
	echo "$i"
	let "i=i+1"
done

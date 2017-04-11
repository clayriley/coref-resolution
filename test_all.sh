#!/bin/bash

# usage: bash tst_all.sh <scorer-metric> <test-dir> <hypotheses-dir-name>


echo `date`
echo "Finding corpus files..."

if [[ $2 == *"/test/"* ]]; then
  test_dir=`find -E "$2" -type f -regex '.+\.v[0-9]_gold_conll'`
else
  test_dir=`find -E "$2" -type f -regex '.+\.v[0-9]_auto_conll'`
fi
# add -E to find in OSX systems!

echo `date`
echo "Evaluating..."

# Evaluate hypotheses
regex="\(([0-9]*\.*[0-9]+) / ([0-9]*\.*[0-9]+)\).+\(([0-9]*\.*[0-9]+) / ([0-9]*\.*[0-9]*\.*[0-9]+)\)"
precision_num=0
precision_den=0
recall_num=0
recall_den=0

for f in $test_dir; 
do
  f_hyp=$(echo $f | awk '{gsub(/\/data\//, "/'"$3"'/")} 1' | awk '{gsub(/\.v[0-9]_.+_.+/, ".hyp")} 1')
  if [ -f $f_hyp ]; then
    if [ $1 = "blanc" ]; then
      results=$(perl ./reference-coreference-scorers-8.01/scorer.pl $1 $f $f_hyp | grep 'BLANC:')
    else
      results=$(perl ./reference-coreference-scorers-8.01/scorer.pl $1 $f $f_hyp | grep 'Coreference:')
    fi
    echo $f_hyp
    echo $results
    if [[ $results =~ $regex ]]; then
      precision_num=$(bc <<< "scale=8; $precision_num+${BASH_REMATCH[3]}")
      precision_den=$(bc <<< "scale=8; $precision_den+${BASH_REMATCH[4]}")
      recall_num=$(bc <<< "scale=8; $recall_num+${BASH_REMATCH[1]}")
      recall_den=$(bc <<< "scale=8; $recall_den+${BASH_REMATCH[2]}")
    else
      echo "something's weird"
    fi
  else
    :
  fi
done

precision=$(bc <<< "scale=4; $precision_num/$precision_den")
recall=$(bc <<< "scale=4; $recall_num/$recall_den")
f1=$(bc <<< "scale=6; (2*$precision*$recall)/($precision+$recall)")
echo "$precision_num/$precision_den = $precision"
echo "$recall_num/$recall_den = $recall"
echo "f-1 = $f1"

echo `date`


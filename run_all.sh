#!/bin/bash

# usage: bash run_all.sh <appendix>
# <appendix> is a string to be appended to output paths--useful for running multiple featuresets simultaneously

SOURCE="../data/conll-2012"
OUT="../output$1/conll-2012"
SAVE="../save.pkl"

echo `date`
echo "Finding corpus files..."

train_dir=`find "$SOURCE/t0" -type f -regex '.+\.v[0-9]_auto_conll'`
#test_dir=`find -E "$SOURCE/test" -type f -regex '.+\.v[0-9]_gold_conll'`
dev_dir=`find "$SOURCE/t1" -type f -regex '.+\.v[0-9]_auto_conll'`
# add -E to find in OSX systems!

#echo $dev_dir


#train_gs="$SOURCE/train/english/annotations/bc/cctv/00/cctv_0001.v4_auto_conll"
#dev_gs="$SOURCE/dev/english/annotations/bc/cctv/00/cctv_0000.v4_auto_conll"

echo `date`
echo "Featurizing trainset..."

# Read trainset, featurize valid instance pairs, write out
for f in $train_dir; 
do
  python2.7 featurize.py $f --train --append $1
done
#python2.7 featurize.py $train_gs --train --append $1

echo `date`
echo "Featurizing testset..."

# Read gold testset, featurize with censored labels, write out
#python2.7 featurize.py $dev_gs --append $1
for f in $dev_dir; 
do
  python2.7 featurize.py $f --append $1
done
#for f in $test_dir; 
#do
#  python2.7 featurize.py $f
#done
# TODO add test

echo `date`
echo "Training and testing..."

# Train classifier on training instances
python2.7 classify.py --svm --train "$OUT/t0" --save $SAVE --consolidate --test "$OUT/t1"
# TODO add "$OUT/test"

echo `date`
echo "Evaluating..."

# Evaluate hypotheses
regex="\(([0-9]+) / ([0-9]+)\).+\(([0-9]+) / ([0-9]+)\)"
precision_num=0
precision_den=0
recall_num=0
recall_den=0
for f in $dev_dir; 
do
  f_hyp=$(echo $f | awk '{gsub(/\/data\//, "/output'"$1"'/")} 1' | awk '{gsub(/\.v[0-9]_.+_.+/, ".hyp")} 1')
  if [ -f $f_hyp ]; then
    results=$(perl ./reference-coreference-scorers-8.01/scorer.pl ceafm $f $f_hyp | grep 'Coreference:')
    echo $f_hyp
    echo $results
    if [[ $results =~ $regex ]]; then
      ((precision_num+="${BASH_REMATCH[3]}"))
      ((precision_den+="${BASH_REMATCH[4]}"))
      ((recall_num+="${BASH_REMATCH[1]}"))
      ((recall_den+="${BASH_REMATCH[2]}"))
    else
      echo "something's weird"
    fi
  else
    :
  fi
done
precision=$(bc <<< "scale=4; $precision_num/$precision_den")
recall=$(bc <<< "scale=4; $recall_num/$recall_den")
f1=$(bc <<< "scale=4; (2*$precision*$recall)/($precision+$recall)")
echo "$precision_num/$precision_den = $precision"
echo "$recall_num/$recall_den = $recall"
echo "f-1 = $f1"


# evaluate based on dev
# evaluate based on test


echo `date`



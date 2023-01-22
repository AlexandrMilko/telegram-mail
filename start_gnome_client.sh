#!/bin/bash
PHONE=$1
TASK=$2
SECONDS_TO_CLOSE=100
echo "BASH: $PHONE - client phone number(session)"
echo "BASH: $TASK - the task of the client."

if [ "$TASK"=="parse" ]
then
  SPLITN=$3
  WORKPART=$4
  PROTESTS_FILE=$5
  echo "BASH: $SPLITN - number of clients to split the work for"
  echo "BASH: $WORKPART - this client part of work"
  python create_client_window.py $PHONE $TASK $SPLITN $WORKPART $PROTESTS_FILE

elif [ "$TASK"=="spam" ]
then
  PROTESTS_FILE=$3
  python create_client_window.py $PHONE $TASK $PROTESTS_FILE

elif [ "$TASK"=="group" ]
then
  PROTESTS_FILE=$3
  GROUP=$4
  python create_client_window.py $PHONE $TASK $PROTESTS_FILE $GROUP
fi

echo "BASH: FINISHED PARSING"
for SEC in $(seq 0 $SECONDS_TO_CLOSE)
do
	echo "BASH: ${SEC}/$SECONDS_TO_CLOSE seconds to be closed"
	sleep 1
done

#!/bin/bash
#
# daily
OPTIONS="--refresh --reindex "
SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
ROOT=$(dirname "$SCRIPTPATH")
LOGDIR="$HOME/logs-trsearch/"

# backup the logs
mkdir -p "$LOGDIR"
cp -n $HOME/logs/search.simson.net/https/*.gz "$LOGDIR"
#
# ingest new articles and then refresh
#
for site in TR BBC ; do
    echo == BEGIN $site ==
    time python3 $ROOT/bin/dbtool.py --site $site  $OPTIONS $1
    echo == END ==
done

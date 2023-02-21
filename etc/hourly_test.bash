#!/bin/bash
#
# daily
OPTIONS="--refresh --reindex "
SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
ROOT=$(dirname "$SCRIPTPATH")
LOGDIR="$HOME/logs-trsearch/"

# https://www.linuxjournal.com/content/sigalrm-timers-and-stdin-analysis

function allow_time
{
   ( #echo timer allowing $1 seconds for execution
     sleep $1
     ps $$ > /dev/null
     if [ ! $? ] ; then
       kill -ALRM $$
     fi
   ) &
}

function timeout_handler
{
   echo Allowable time for execution exceeded.
   exit 1
}


function webtest () {
    #echo
    #echo $1
    STATUSCODE=$(curl --silent --output /dev/null --write-out "%{http_code}" $1)
    if test $STATUSCODE -ne 200; then
        echo curl error $STATUSCODE: $1
    fi
}

trap timeout_handler SIGALRM
allow_time 10
# This generates a 404:
# webtest 'https://downloads.digitalcorpora.org/aasdfasd'
webtest 'https://downloads.digitalcorpora.org/'
webtest 'https://downloads.digitalcorpora.org/search'
webtest 'https://downloads.digitalcorpora.org/search/api?q=dmg'

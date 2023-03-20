#!/bin/bash
#
# deploy
SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
ROOT=$(dirname "$SCRIPTPATH")
LOGDIR="$HOME/logs-trsearch/"

cd $ROOT/..
git pull --recurse-submodules
make install-dependencies
make touch

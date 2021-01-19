#!/bin/bash

pip3 install --user .

USER_BASE_BIN=$(python3 -m site --user-base)/bin
export PATH="$USER_BASE_BIN:$PATH"

nearup run betanet
nearup stop

watcher run betanet '~/.near/betanet/' --force-restart &

sleep 5m

curl --retry-delay 5 --retry 10 --fail http://localhost:3030/status

nearup stop

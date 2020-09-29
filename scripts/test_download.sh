# TODO: https://github.com/near/nearup/issues/131

pip3 install --user .

export PATH="$HOME/.local/bin:$PATH"

nearup run betanet
nearup stop

watcher run betanet '~/.near/betanet/' --force-restart &

sleep 5m

curl --retry-delay 5 --retry 10 --fail http://localhost:3030/status

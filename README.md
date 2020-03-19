# nearup
Public scripts to launch near devnet, betanet and testnet node

# Usage
## Install
```
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/nearprotocol/nearup/master/nearup | python3
```
Nearup automatically add itself to PATH and self update to latest version

## Start devnet, betanet, testnet
```
nearup devnet
nearup betanet
nearup testnet
```

## Start devnet, betanet, testnet with officially compiled binary
Currently Linux only:
```
nearup {devnet, betanet, testnet} --nodocker
```

## Start devnet, betanet, testnet with local nearcore
```
# compile in nearcore/ with `make release` or `make debug` first
nearup {devnet, betanet, testnet} --nodocker --binary-path path/to/nearcore/target/{debug, release}
```

## Stop a running node
```
nearup stop
```

## Additional options
```
nearup {devnet, betanet, testnet} --help
```
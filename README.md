# nearup

[![PyPI version](https://badge.fury.io/py/nearup.svg)](https://pypi.org/project/nearup/)

Public scripts to launch near betanet and testnet node

# Usage

## Prerequisite

Before you proceed, make sure you have the following software installed:

* Python 3 and Pip3

### Ubuntu Prerequisite Installation

Here is the installation command:

```
sudo apt update
sudo apt install python3 && python3-pip
```

## Install

```
pip3 install nearup
```

Nearup automatically adds itself to PATH: restart the terminal, or issue the command `source ~/.profile`.
On each run, nearup self-updates to the latest version.

## Start

### Using Officially Compiled Binary (recommended for running on servers)

Currently, officially compiled binaries are available for Linux and Mac OS X

```
nearup run betanet
```

Replace `betanet` with `testnet` if you want to use a different network.

### Using Locally Compiled Binary (recommended for security critical validators or development needs)

Clone and compile nearcore with `make release` or `make debug` first.

```
nearup run betanet --binary-path path/to/nearcore/target/{debug, release}
```

Replace `betanet` with `testnet` if you want to use a different network.

## Spawn Local network

Clone and compile nearcore with `make release` or `make debug` first.

```
nearup run localnet --binary-path path/to/nearcore/target/{debug, release}
```

By default it will spawn 4 nodes validating in 1 shard.
RPC ports of each nodes will be consecutive starting from 3030.
Access one node status using http://localhost:3030/status

## Stop a Running Node or all running nodes in local network

```
nearup stop
```

## Additional Options

```
nearup run betanet --help
```


If the process is completed without errors, the node will be in sync within a few minutes.

### Cleaning up
This is the step-by-step guide to remove nearup from your macOS system:

1. Stop nearcore container
	```
	nearup stop
	```
	The output will be `Stopping docker near`

2. Remove .near folder with the command
	```
	rm ~/-rf .near
	```

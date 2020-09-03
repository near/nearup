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
sudo apt install python3 python3-pip
```

:warning:  Upgrade pip if needed you are getting a Permission Denied error or version of pip (pip3 --version) is below 20.
```
pip3 install --upgrade pip
```
## Install
:warning: Make sure that you are installing with the --user flag
```
pip3 install --user nearup
```

:warning: Verify that you local installation is in ~/.local/bin/nearup by running:
```
which nearup
```

:warning: Add nearup to your PATH in ~/.profile or ~/.bashrc or appropriate shell config
```
export PATH="$HOME/.local/bin:$PATH"
```

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

# Docker
## Building the docker image
```
docker build . -t nearup
```

## Running nearup with Docker
:warning: Nearup and neard are running inside the container, to ensure you don't lose your data which should live on the host you have to mount the ~/.near folder.
```
To run the nearup docker image run:
```
docker run --volume $HOME/.near:/root/.near nearup run betanet
```

## To run in the detached(deamon) mode run:
```
docker run --mount type=bind,source=$HOME/.near,target=/root/.near nearup nearup run testnet
```

## You can get the information about the running docker container with:
```
docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS           PORTS               NAMES
fc17f7f7fae0        nearup              "/root/start.sh run …"   3 minutes ago       Up 3 minutes     324324         mystifying_moore
```

To execute other nearup commands like start,stop  and logs you can use:

:warning: The container is running in a busy wait loop, so the container won't die.
```
docker exec <container-id> nearup logs
docker exec <container-id> nearup stop
docker exec <container-id> nearup run {betanet/testnet}
```

To eventually kill the docker container run:
```
docker kill <container-id>
```

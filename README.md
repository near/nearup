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

## Upgrade
:warning:  If you have already installed nearup, you can upgrade to the latest version by using the command below
```
pip3 install --user --upgrade nearup
```

## Start

### Using Officially Compiled Binary (recommended for running on servers)

Currently, officially compiled binaries are available for Linux and Mac OS X

```
nearup run betanet
```

To run a validator node with validator keys, please specify the account id:
```
nearup run betanet --account-id testing.account
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
docker build . -t nearprotocol/nearup
```
or 
## Pull the docker image
```
docker pull nearprotocol/nearup
```

## Running nearup with Docker
:warning: Nearup and neard are running inside the container, to ensure you don't lose your data which should live on the host you have to mount the ~/.near folder.
To run the nearup docker image run:
```
docker run -v $HOME/.near:/root/.near --name nearup nearprotocol/nearup run betanet
```

## To run in the detached(deamon) mode run:
```
docker run -v $HOME/.near:/root/.near -d --name nearup nearprotocol/nearup run betanet
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
docker exec nearup nearup logs
docker exec nearup nearup stop
docker exec nearup nearup run {betanet/testnet}
```

To get the neard logs run:
```
docker exec nearup nearup logs
or
docker exec nearup nearup logs --follow
```
To get the nearup logs run:
```
docker logs -f nearup
```

To eventually kill the docker container run:
```
docker kill nearup
```

# Development

Currently, nearup expects the test environment to be run on Linux.

For macOS, you can simulate a Linux environment with docker.

To build a development image,

```
docker build . -t nearprotocol/nearup:dev
```

The following will mount your repo directory into the running container and drop you into a shell to run test commands.

```
docker run -it --entrypoint "" -v $PWD:/root/nearup -v $HOME/.near:/root/.near -w /root/nearup nearprotocol/nearup:dev bash
```

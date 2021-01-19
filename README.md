# nearup

[![PyPI version](https://badge.fury.io/py/nearup.svg)](https://pypi.org/project/nearup/)

Launch NEAR `betanet` and `testnet` nodes.

- [Prepare](#prepare)
- [Install](#install)
  * [Upgrade](#upgrade)
- [Getting Started](#getting-started)
  * [Using the official binary](#using-the-official-binary)
  * [Using a locally compiled binary](#using-a-locally-compiled-binary)
  * [Spawn a local network](#spawn-a-local-network)
- [Operating](#operating)
  * [Stop a running node or all running nodes in local network](#stop-a-running-node-or-all-running-nodes-in-local-network)
  * [Additional options](#additional-options)
- [Docker](#docker)
  * [Building the docker image](#building-the-docker-image)
  * [Pull the docker image](#pull-the-docker-image)
  * [Running `nearup` with Docker](#running-nearup-with-docker)
    + [Running in detached mode](#running-in-detached-mode)
  * [Check if the container is running](#check-if-the-container-is-running)
  * [Execute `nearup` commands in container](#execute-nearup-commands-in-container)
  * [`nearup` logs](#nearup-logs)
  * [Stop the docker container](#stop-the-docker-container)
- [Development](#development)
  * [Common commands](#common-commands)

## Prepare

Before you proceed, make sure you have `Python 3` and `pip3` installed.

On ubuntu, you can install with,

```
sudo apt update
sudo apt install python3 python3-pip python3-dev
```

:warning: Upgrade pip if needed you are getting a Permission Denied error or version of pip (pip3 --version) is below 20.

```
pip3 install --upgrade pip
```

## Install

:warning: Make sure that you are installing with the `--user` flag.

```
pip3 install --user nearup
```

Verify that you local installation is in `python3 -m site --user-base` under bin directory by running:

```
which nearup
```

:warning: If the above returns nothing, add `nearup` to your `$PATH` in `~/.profile`, `~/.bashrc`, or appropriate shell config.

```
USER_BASE_BIN=$(python3 -m site --user-base)/bin
export PATH="$USER_BASE_BIN:$PATH"
```

### Upgrade

:warning: If you have already installed `nearup`, you can upgrade to the latest version by using the command below

```
pip3 install --user --upgrade nearup
```

## Getting Started

### Using the official binary

**This is recommended for running on servers**

You can start your node with:

```
nearup run betanet
```

To run a validator node with validator keys, please specify the account id:

```
nearup run betanet --account-id testing.account
```

Replace `betanet` with `testnet` if you want to use a different network.

### Using a locally compiled binary

**Recommended for security critical validators or during development.**

Clone and compile nearcore with `make release` or `make debug` first.

```
nearup run betanet --binary-path path/to/nearcore/target/{debug, release}
```

Replace `betanet` with `testnet` if you want to use a different network.

### Spawn a local network

Clone and compile nearcore with `make release` or `make debug` first.

```
nearup run localnet --binary-path path/to/nearcore/target/{debug, release}
```

By default it will spawn 4 nodes validating in 1 shard.
RPC ports of each nodes will be consecutive starting from 3030.
Access one node status using http://localhost:3030/status

## Operating

### Stop a running node or all running nodes in local network

```
nearup stop
```

### Additional options

```
nearup run betanet --help
```

## Docker

### Building the docker image

```
docker build . -t nearprotocol/nearup
```

### Pull the docker image

If you don't want to build a docker image locally, you can pull the `latest` from Docker Hub,

```
docker pull nearprotocol/nearup
```

### Running `nearup` with Docker

:warning: `nearup` and `neard` are running inside the container, to ensure you don't lose your data which should live on the host you have to mount the ~/.near folder.
To run the `nearup` docker image run:

```
docker run -v $HOME/.near:/root/.near --name nearup nearprotocol/nearup run betanet
```

#### Running in detached mode

To run `nearup` in docker's detached (non-blocking) mode, you can add `-d` to the `docker run` command,

```
docker run -v $HOME/.near:/root/.near -d --name nearup nearprotocol/nearup run betanet
```

### Check if the container is running

```
docker ps
```

```
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS           PORTS               NAMES
fc17f7f7fae0        nearup              "/root/start.sh run …"   3 minutes ago       Up 3 minutes     324324         mystifying_moore
```

### Execute `nearup` commands in container

To execute other `nearup` commands like `logs`, `stop`, `run`, you can use `docker exec`,

```
docker exec nearup nearup logs
docker exec nearup nearup stop
docker exec nearup nearup run {betanet/testnet}
```

(The container is running in a busy wait loop, so the container won't die.)

### `nearup` logs

To get the `neard` logs run:

```
docker exec nearup nearup logs
```

or,

```
docker exec nearup nearup logs --follow
```

To get the `nearup` logs run:

```
docker logs -f nearup
```

### Stop the docker container

```
docker kill nearup
```

## Development

To build a development image:

```
docker build . -t nearprotocol/nearup:dev
```

The following will mount your repo directory into the running container and drop you into a shell to run test commands.

```
docker run -it --entrypoint "" -v $PWD:/root/nearup -v $HOME/.near:/root/.near -w /root/nearup nearprotocol/nearup:dev bash
```

### Common commands

For testing and other checks, `nearup` uses `tox`.

To install,

```
pip3 install --user tox
```

**Unit tests**

```
tox
```

**Unit tests w/ coverage**

```
tox -e coverage
```

**Linter checks**

```
tox -e lint
```

**Python style checks**

```
tox -e style
```

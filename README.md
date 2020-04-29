# nearup

Public scripts to launch near devnet, betanet and testnet node

# Usage

## Prerequisite

Before you proceed, make sure you have the following software installed:

* Python 3
* git (used for updates)
* cURL (installation only)

### Ubuntu Prerequisite Installation

Here is the installation command:

```
sudo apt install python3 git curl
```

## Install

```
curl --proto '=https' --tlsv1.2 -sSfL https://up.near.dev | python3
```

Nearup automatically adds itself to PATH: restart the terminal, or issue the command `source ~/.profile`.
On each run, nearup self-updates to the latest version.

## Start

### Using Docker (recommended for fast onboarding)

> Heads up, you need [Docker](https://docs.docker.com/get-docker/) installed before you proceed.
> Ubuntu users can install it with the following command:
>
> ```
> sudo apt install docker.io
> ```
>
> Also, you need to make sure that your user belongs to `docker` group:
>
> ```
> sudo usermod -aG docker your-user
> ```

Once all the prerequisites are met, just run:

```
nearup betanet
```

Where `betanet` is the weekly release; use `devnet` for the nightly releases, or `testnet` for the stable releases.

### Using Officially Compiled Binary (recommended for running on servers)

Currently, officially compiled binaries are available for Linux and Mac OS X

```
nearup betanet --nodocker
```

Replace `betanet` with `devnet` or `testnet` if you want to use a different network.

### Using Locally Compiled Binary (recommended for security critical validators or development needs)

Clone and compile nearcore with `make release` or `make debug` first.

```
nearup betanet --nodocker --binary-path path/to/nearcore/target/{debug, release}
```

Replace `betanet` with `devnet` or `testnet` if you want to use a different network.

## Spawn Local network

Clone and compile nearcore with `make release` or `make debug` first.

```
nearup localnet --binary-path path/to/nearcore/target/{debug, release}
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
nearup betanet --help
```

# Contributions
To change code and run local version of nearup:
1. fork/clone this repo and checkout to your branch
2. change code
3. run `python3 main.py <net> ...`. If your changes merge to master branch, this will be equivalent to `nearup <net> ...`

# Get Started Guides

## Run nearup on macOS
nearup runs also on Apple macOS. Requirements:
- At least 40GB of storage space
- [Docker for Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac/)
- Xcode Command Line Tools
- [Python3](https://www.python.org/downloads/) *No need to install with macOS 10.15 Catalina*

### Start a Node

1. **Important:** launch `Docker` from your Applications folder. You don't need a Docker Hub account to run nearup

2. If you haven't already, install Xcode Command Line Tools
	```
	xcode-select --install
	```

2. Download nearup via `curl`
	```
	curl --proto '=https' --tlsv1.2 -sSfL https://up.near.dev | python3
	```
	The output shoud be `Nearup is installed to ~/.nearup!`. 
	You may receive an alert to install or update Xcode Command Line Tools. Follow the steps. Once completed, try again the command above.

3. Restart the terminal, or issue the command 
	```
	source ~/.profile
	```
	No output is expected.

4. Launch the nearup with the command
	```
	nearup betanet
	```
	The output will look like this:
	```
	Pull docker image nearprotocol/nearcore:beta
	Setting up network configuration.
	Enter your account ID (leave empty if not going to be a validator): lakecat
	Generating node key...
	Node key generated
	Generating validator key...
	Validator key generated
	Stake for user 'lakecat' with 'ed25519:HigQXU4QkAvfsuMPTyL5f65coWnCAkR4Yi7RiJPcQKNv'
	Starting NEAR client docker...
	Node is running! 
	To check logs call: docker logs --follow nearcore
	```
	Nearup will ask your `account ID`, for now you can leave it empty. If you already have a wallet on https://wallet.betanet.nearprotocol.com, feel free to input your `account ID` for future use as a validator.

5. Check if your node is running correctly by issuing the command
	```
	docker logs --follow nearcore --tail 100
	```
	The output will look like this:
	```
	Telemetry: https://explorer.nearprotocol.com/api/nodes
	Bootnodes: 
	Mar 25 01:38:59.607  INFO near: Did not find "/srv/near/data" path, will be creating new store database    
	Mar 25 01:39:00.161  INFO stats: Server listening at ed25519:AWDhVpfVDvV85tem2ZUa6CmZQwmPawFuzR1wnoiLirRa@0.0.0.0:24567
	Mar 25 01:39:10.598  INFO stats: #       0 Downloading headers 0% -/4  5/5/40 peers ⬇ 57.9kiB/s ⬆ 0.8kiB/s 0.00 bps 0 gas/s CPU: 42%, Mem: 39.2 MiB    
	Mar 25 01:39:20.798  INFO stats: #       0 Downloading headers 2% -/4  5/5/40 peers ⬇ 144.0kiB/s ⬆ 0.9kiB/s 0.00 bps 0 gas/s CPU: 49%, Mem: 50.5 MiB    
	Mar 25 01:39:30.800  INFO stats: #       0 Downloading headers 3% -/4  5/5/40 peers ⬇ 239.9kiB/s ⬆ 0.9kiB/s 0.00 bps 0 gas/s CPU: 46%, Mem: 58.8 MiB    
	Mar 25 01:39:40.804  INFO stats: #       0 Downloading headers 4% -/4  5/5/40 peers ⬇ 335.6kiB/s ⬆ 1.0kiB/s 0.00 
	```

	If you need to export the logs for troubleshooting, issue the command:
	```
	docker logs nearcore --tail 5000 2>&1 | tee nearcore$(date +"%Y%m%d%H%M").log
	```
	This command will generate a file in your current folder called 'nearcoreYYYYMMDDHHMM.log' containing the last 5,000 lines of nearcore logs. You can change the switch `--tail 5000` to any other number to export more or less data.

### Updating the node
Nearup provides an automated process to verify that your node is using the current network, by analyzing `genesis.json`. If your node is not up to date, it will not be able to dowload new blocks, and will disconnect automatically:
```
Apr 10 18:10:15.873 ERROR network: Attempting to connect to a node (ed25519:GkDv7nSMS3xcqA45cpMvFmfV1o4fRF6zYo1JRR6mNqg5@0.0.0.0:24567@node2) with a different genesis block. Our genesis: GenesisId { chain_id: "betanet", hash: `BAtdJLUtNabWVJnnvYUuot7TfRf9VcqKh4b8FKAXbXSD` }, their genesis: GenesisId { chain_id: "betanet", hash: `3MKug5MgUnBYBeymCL8P9KXYSJoAhTfcKJzhPKPo8iXQ` }
```

To automatically update your node, stop nearup:
```
nearup stop
```
Wait a few seconds, and restart nearup:
```
nearup betanet
```
The output will show a new genesis checksum:
```
Warning: current deployed version on betanet is 650b69863207ac6be5b55d2b2f8761dc89821b49, but local binary is 56622f45. It might not work
Remote genesis protocol version md5 997a44a7b94fdb680d87548d7dd9a572, ours is 309f5819133d4399f4a0bab054fa3c38
Update genesis nearkat with 'ed25519:A5DL4iByp1EbYYpRVrpoKwBBA5YKkPdK6L1hLsTmcQrv'
Starting NEAR client...
```

If the process is completed without errors, the node will be in sync within a few minutes.

### Cleaning up
This is the step-by-step guide to remove nearup from your macOS system:

1. Stop nearcore container
	```
	nearup stop
	```
	The output will be `Stopping docker near`

2. Prune Docker 
	**warning:** you may want to skip this step if you have other containers on your system
	```
	docker system prune --volumes
	```
	The output will require your confirmation
	```
	WARNING! This will remove:
	  - all stopped containers
	  - all networks not used by at least one container
	  - all volumes not used by at least one container
	  - all dangling images
	  - all dangling build cache
	Are you sure you want to continue? [y/N]
	```

3. Open your `$HOME` directory
	```
	cd $home
	```

4. Remove .near folder with the command
	```
	rm -ri .near
	```
	The output will require your confirmation to delete every file and folder
	```
	Nearkats-MacBook-Pro:.nearup nearkat$ rm -ri $HOME/.near
	examine files in directory /Users/nearkat/.near? yes
	remove /Users/nearkat/.near/genesis.json? yes
	remove /Users/nearkat/.near/config.json? yes
	remove /Users/nearkat/.near/node_key.json? yes
	examine files in directory /Users/nearkat/.near/data? yes
	remove /Users/nearkat/.near/data/IDENTITY? y
	remove /Users/nearkat/.near/data/000003.log? y
	remove /Users/nearkat/.near/data/LOCK? y
	remove /Users/nearkat/.near/data/OPTIONS-000078? y
	remove /Users/nearkat/.near/data/CURRENT? y
	remove /Users/nearkat/.near/data/LOG? y
	remove /Users/nearkat/.near/data/MANIFEST-000004? y
	remove /Users/nearkat/.near/data/OPTIONS-000080? y
	remove /Users/nearkat/.near/data? y
	remove /Users/nearkat/.near/validator_key.json? y
	remove /Users/nearkat/.near? y
	```
	You may save the LOG directory for future use. Alternatively, you can use `rm -rf .near` to skip any confirmation.

5. Eventually uninstall `Docker`, by moving it from applications folder to the trash
6. Eventually uninstall Xcode Command Line Tools by removing the folder `/Library/Developer/CommandLineTools` - from the [official Apple guide](https://developer.apple.com/library/archive/technotes/tn2339/_index.html#//apple_ref/doc/uid/DTS40014588-CH1-HOW_CAN_I_UNINSTALL_THE_COMMAND_LINE_TOOLS_)

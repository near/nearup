# nearup
Public scripts to launch near devnet, betanet and testnet node

# Usage
## Install
```
curl --proto '=https' --tlsv1.2 -sSfL https://up.near.dev | python3
```
Nearup automatically add itself to PATH. And on each run, it self updates to latest version.

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

## OSx Instructions to test NEAR Betanet on your Macbook Pro
Nearup runs also on Apple OSx. Requirements:
- At least 40GB of HDD space available
- [Install Python3 by using this link](https://www.python.org/downloads/)
- [Install Docker for Mac by using this link](https://hub.docker.com/editions/community/docker-ce-desktop-mac/)
- Xcode (installation will start automatically during the installation process)

### Step by step Guide:
1. Be sure that you installed the latest version of Python3 and Docker, by opening the links in the requirements above

2. **Important:** first launch `Docker` from your Applications folder, or your Launchpad. No worries: you won't require a Docker Hub account to use it, so feel free to skip the login part (we simply need Docker installed on your laptop)

3. Open Spotlight by pressing `⌘command` and `spacebar` buttons together

4. Type `terminal` and press `enter`. You should see a new window with text similar to this one:
	```
	Last login: Tue Mar 24 18:06:46 2020
	Nearkats-MacBook-Pro:~ nearkat$ 
	```
	Alternatively, you can ask Siri `open terminal`, it works too!

5. In the Terminal screen, type `curl --proto '=https' --tlsv1.2 -sSfL https://up.near.dev | python3` (feel free to copy and paste, by using the usual copy&paste `⌘c` and `⌘v`):
	```
	Nearkats-MacBook-Pro:~ nearkat$ curl --proto '=https' --tlsv1.2 -sSfL https://up.near.dev | python3
	Nearup is installed to ~/.nearup!
	```
	You may receive an alert to install Xcode. Follow the steps. Once completed, try again to copy and paste the command above.

6. Open the Nearup folder: `cd $HOME/.nearup`:
	```
	Nearkats-MacBook-Pro:.nearup nearkat$ 
	```

7. Start the node by typing the command `./nearup betanet --verbose`:
	```
	Nearkats-MacBook-Pro:.nearup nearkat$ ./nearup betanet --verbose
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
	Nearup will ask your `account ID`, but you can leave it empty by now. If you have already a wallet on https://wallet.betanet.nearprotocol.com, feel free to use your existing account ID - for future use as a validator.

9. Check if your node is running correctly: `docker logs --follow nearcore`
	```
	Nearkats-MacBook-Pro:.nearup nearkat$ docker logs --follow nearcore
	Telemetry: https://explorer.nearprotocol.com/api/nodes
	Bootnodes: 
	Mar 25 01:38:59.607  INFO near: Did not find "/srv/near/data" path, will be creating new store database    
	Mar 25 01:39:00.161  INFO stats: Server listening at ed25519:AWDhVpfVDvV85tem2ZUa6CmZQwmPawFuzR1wnoiLirRa@0.0.0.0:24567
	Mar 25 01:39:10.598  INFO stats: #       0 Downloading headers 0% -/4  5/5/40 peers ⬇ 57.9kiB/s ⬆ 0.8kiB/s 0.00 bps 0 gas/s CPU: 42%, Mem: 39.2 MiB    
	Mar 25 01:39:20.798  INFO stats: #       0 Downloading headers 2% -/4  5/5/40 peers ⬇ 144.0kiB/s ⬆ 0.9kiB/s 0.00 bps 0 gas/s CPU: 49%, Mem: 50.5 MiB    
	Mar 25 01:39:30.800  INFO stats: #       0 Downloading headers 3% -/4  5/5/40 peers ⬇ 239.9kiB/s ⬆ 0.9kiB/s 0.00 bps 0 gas/s CPU: 46%, Mem: 58.8 MiB    
	Mar 25 01:39:40.804  INFO stats: #       0 Downloading headers 4% -/4  5/5/40 peers ⬇ 335.6kiB/s ⬆ 1.0kiB/s 0.00 bps 0 gas/s CPU: 56%, Mem: 68.1 MiB    
	Mar 25 01:39:50.807  INFO stats: #       0 Downloading headers 5% -/4  5/5/40 peers ⬇ 421.9kiB/s ⬆ 1.1kiB/s 0.00 bps 0 gas/s CPU: 47%, Mem: 75.3 MiB    
	Mar 25 01:40:00.810  INFO stats: #       0 Downloading headers 6% -/4  5/5/40 peers ⬇ 508.3kiB/s ⬆ 1.2kiB/s 0.00 bps 0 gas/s CPU: 48%, Mem: 81.7 MiB    
	Mar 25 01:40:10.810  INFO stats: #       0 Downloading headers 7% -/4  5/5/40 peers ⬇ 479.8kiB/s ⬆ 0.8kiB/s 0.00 bps 0 gas/s CPU: 33%, Mem: 86.4 MiB    
	Mar 25 01:40:20.814  INFO stats: #       0 Downloading headers 7% -/4  5/5/40 peers ⬇ 442.0kiB/s ⬆ 0.4kiB/s 0.00 bps 0 gas/s CPU: 33%, Mem: 91.0 MiB    
	Mar 25 01:40:31.570  INFO stats: #       0 Downloading headers 8% -/4  5/5/40 peers ⬇ 394.8kiB/s ⬆ 0.4kiB/s 0.00 bps 0 gas/s CPU: 38%, Mem: 96.4 MiB    
	Mar 25 01:40:42.122  INFO stats: #       0 Downloading headers 9% -/4  5/5/40 peers ⬇ 348.0kiB/s ⬆ 0.4kiB/s 0.00 bps 0 gas/s CPU: 41%, Mem: 101.8 MiB    
	Mar 25 01:40:52.124  INFO stats: #       0 Downloading headers 9% -/4  5/5/40 peers ⬇ 329.1kiB/s ⬆ 0.4kiB/s 0.00 bps 0 gas/s CPU: 49%, Mem: 107.5 MiB    
	Mar 25 01:41:03.005  INFO stats: #       0 Downloading headers 10% -/4  5/5/40 peers ⬇ 319.7kiB/s ⬆ 0.3kiB/s 0.00 bps 0 gas/s CPU: 52%, Mem: 113.7 MiB    
	Mar 25 01:41:13.008  INFO stats: #       0 Downloading headers 11% -/4  5/5/40 peers ⬇ 348.1kiB/s ⬆ 0.3kiB/s 0.00 bps 0 gas/s CPU: 59%, Mem: 120.1 MiB    
	Mar 25 01:41:23.013  INFO stats: #       0 Downloading headers 12% -/4  5/5/40 peers ⬇ 358.0kiB/s ⬆ 0.4kiB/s 0.00 bps 0 gas/s CPU: 51%, Mem: 125.8 MiB
	```
	If you want to exit, just press `⌃control` and `c` together, and close your terminal window

### Cleaning up:
In order to remove NEAR Betanet node and reclaim disk space, you have to:

1. Open again a `terminal` window (ask again to Siri, or use Spotlight)
2. Type again the command:
	```
	cd $HOME/.nearup
	```
3. Stop nearup `./nearup stop`:
	```
	Nearkats-MacBook-Pro:.nearup nearkat$ ./nearup stop
	Stopping docker near
	```
4. Open the folder `cd $HOME`
5. Reclaim disk space by removing .near folder, by typing the command `rm -ri .near`. Press `yes` or `y` to confirm that you want to delete the files:
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
	WARNING: `rm` command is an **extremely powerful** and **dangerous** command to delete files, so you don't really want to use it unless you know what you are doing. Please DOUBLE CHECK that you are deleting `.near` folder, and not something else!
6. Remove `Docker`, by simply moving it from your applications folder to the trash



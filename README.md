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
./nearup devnet
./nearup betanet
./nearup testnet
```
Where `devnet` is the nightly release; `betanet` is the weekly release; `testnet` the stable release with monthly releases.

## Start devnet, betanet, testnet with officially compiled binary
Currently Linux only:
```
./nearup betanet --nodocker
```
Replace `betanet` with the network you want to use

## Start devnet, betanet, testnet with local nearcore
```
# compile in nearcore/ with `make release` or `make debug` first
./nearup {devnet, betanet, testnet} --nodocker --binary-path path/to/nearcore/target/{debug, release}
```

## Stop a running node
```
./nearup stop
```

## Additional options
```
nearup {devnet, betanet, testnet} --help
```

## macOS Instructions to test NEAR Betanet on your MacBook Pro
Nearup runs also on Apple macOS. Requirements:
- At least 40GB of HDD space available
- [Install Docker for Mac by using this link](https://hub.docker.com/editions/community/docker-ce-desktop-mac/)
- Xcode Command Line Tools (installation will start automatically during the process)
- If you are not using macOS 10.15 Catalina, [install Python3 from this link](https://www.python.org/downloads/)

### Step by step Guide:

1. **Important:** first launch `Docker` from your Applications folder. You don't need a Docker Hub account to run nearup

2. Issue the command `curl --proto '=https' --tlsv1.2 -sSfL https://up.near.dev | python3`
	```
	Nearkats-MacBook-Pro:~ nearkat$ curl --proto '=https' --tlsv1.2 -sSfL https://up.near.dev | python3
	Nearup is installed to ~/.nearup!
	```
	You may receive an alert to install Xcode Command Line Tools. Follow the steps. Once completed, try again to copy and paste the command above.

3. Restart the terminal, or issue the command `source ~/.profile`

4. Launch the nearup with the command `./nearup betanet --verbose`:
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
	Nearup will ask your `account ID`, you can leave it empty by now. If you have already a wallet on https://wallet.betanet.nearprotocol.com, feel free to use your account ID for future use as a validator.

5. Check if your node is running correctly: `docker logs --follow nearcore`
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

### Cleaning up:
In order to remove NEAR Betanet node and reclaim disk space, you have to:

1. Stop nearup `./nearup stop`:
	```
	Nearkats-MacBook-Pro:.nearup nearkat$ ./nearup stop
	Stopping docker near
	```
2. Be sure to open the correct directory: `cd $HOME`
3. Reclaim disk space by removing .near folder, by typing the command `rm -ri .near`. Press `yes` or `y` to confirm that you want to delete the files:
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
	You may save the LOG directory for future use. As a faster alternative, you can use `rm -rf .near`
4. Remove `Docker`, by simply moving it from your applications folder to the trash



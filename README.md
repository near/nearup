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
- [Python3](https://www.python.org/downloads/)
- [Docker for Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac/)
- Xcode (installation starts automatically)

1. Install the latest version of Python3 and Docker, by opening the links in the requirements
2. Open a terminal window (press `CMD` anb `spacebar` buttons together)
3. Type `terminal` and press `enter`. You should see a new window with the following text:
	```
	Last login: Tue Mar 24 18:06:46 2020
	Nearkats-MacBook-Pro:~ nearkat$ 
	```
4. In the Terminal screen, type
```
curl --proto '=https' --tlsv1.2 -sSfL https://up.near.dev | python3
```
If you haven't yet, you will receive an alert to install Xcode. Once completed, try again to execute the command above.
5. Open the Nearup folder:
```
cd $HOME/.nearup
```
6. Start the node by typing the command:
```
nearup betanet --verbose
```
7. Nearup will ask your `account id`, you can keep it empty by now
8. Check how's your node is doing:
```
docker logs --follow nearcore
```



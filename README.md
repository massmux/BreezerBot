# BreezerBot

Pythonic Breez implementation for Telegram

This software implements Breez SDK and makes then possible to have a non custodial wallet connected to a Greenlight node. The magic is that you own the keys but you dont have to worry about channels, liquidity and balances.

## Installation

### get the Telegram API Key

open Telegram with your account and use Botfather. Create a new Bot (with name and username you want), take the resulting API Key to be put in the settings file of your software installation

### software installation

```
git clone https://github.com/massmux/BreezerBot.git
cd BreezerBot
```

configure the files:

- settings.ini . In this file the Telegram Bot API key is necessary
- secrets.txt this contains your secrets (seed phrase and access keys to the Breez system)

the docker containers may be built or downloaded from docker hub. In first case the building may take a long time. Please bear in mind that images will be quite big (because of the bindings). You have to consider to have aroung 11 GB free on your system.

to build
```
docker build -t massmux/breezerbot .
```

to get from the repository

```
docker pull massmux/breezerbot
```

### Run

from inside the package dir (where your docker-compose file is in place):

```
docker-compose up -d
```

Now start with your wallet on Telegram

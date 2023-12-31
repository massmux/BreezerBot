# BreezerBot

Pythonic Breez implementation for Telegram

This software implements Breez SDK and makes then possible to have a non custodial wallet connected to a Greenlight node. The magic is that you own the keys but you dont have to worry about channels, liquidity and balances.

## Installation

### Get the Telegram API Key

In order to register a new Bot on Telegram, just open Telegram with your account and use Botfather. Create a new Bot (with name and username you want), take the resulting API Key to be put in the settings file of your software installation

### Software installation

```
git clone https://github.com/massmux/BreezerBot.git
cd BreezerBot
```

configure the settings.ini file :

- Telegram API from bothfather
- Breez SDK: API key

The latest version is based on the python Library of Breez SDK, so smaller than previous Breezer implementations.

Invite code and phrase have to be set in redis at the moment. We will remove this in the next features for a different way.

to build
```
docker build -t massmux/breezerbot .
```

Otherwise you can get from from the repository, pulling the image

```
docker pull massmux/breezerbot:0.2.9.post3
```

### Run

from inside the package dir (where your docker-compose file is in place):

```
docker-compose up -d
```

Now start with your wallet on Telegram

## Features

At the moment we implemented the following features:

- Get balance and status
- Generation of Lightning invoice and payment detect
- Payment of a Lightning invoice

## Thanks

Thanks to tmrwapp for snippets and ideas.

Thanks to the Breez SDK team https://github.com/breez/breez-sdk

## Disclaimer

This software is in early stage. Use at your own risk. No liability is take for any action with this software. This software is Open Source software.

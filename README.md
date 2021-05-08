# cssh

My [ContainerSSH](https://containerssh.io/) setup to host Linux learning environment using Telegram bot as registration facility.



[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/tterb/atomic-design-ui/blob/master/LICENSEs)
  
## Rationale

ContainerSSH seemed like a **normal** way to solve the problem of hosting a platform for teaching Linux. 

My previous solution was a collection of hacks that kinda worked, 
but had lots of problems, like a lot of time to deploy
a single image, definitely some security issuess, no process management in containers...
You name it. And all of that using bash scripts. Definitely not worth publishing.

Unfortunately, ContainerSSH has not-so-great docs, no sane default configuration and the examples are broken. Here comes this repo.
## Deployment

To run on a single host should add your bot's token to .env file for docker-compose to use, like that:

```bash
BOT_TOKEN=HELLO_THIS_IS_TOKEN
```

And fix admin's ID in bot's source code (will be fixed soon).

Compose will source `.env` file before startup. Then just

```bash
  sudo docker-compose up -d
```
To actually run it (or without sudo if current user is in `docker` group)

  
## Usage

`docker-compose` will deploy containerssh ssh service 
alongside with Telegram bot. 

SSH is listening on port 2222 by default. 

All Telegram bot's users have these commands:

`/reg` - register in the system, choose username and get a password.

`/creds` - remind user who he is and what is his password

`/images` - get keyboard of all images to choose which one to get on SSH connect

Admin additionally can:

`/add_image <imagename>` - allow access to these image. Image should be present on the host machine.

`/del_image <imagename>` - delete access to this image for users.

  
## Roadmap

- MVP is near but not ready, yikes.

- Easy-to-deploy public key authentication for docker socket, not an abysmal 100-something lines of bash copypasta. [CFSSL](https://github.com/cloudflare/cfssl), maybe?

- Improvements of bot's UI.

- I still have no idea how to properly test Telegram bots. Maybe you can help?

- Less hardcoded values, configuration template.

- Dockerfile template for image to deploy by containerssh (WIP).


  
## Features

- Small disk footprint (distroless as base images for services)

- One command deploy.

- Template optimized for learning scenarios and feels more like an actual machine than a container.

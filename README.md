# cssh

My [ContainerSSH](https://containerssh.io/) setup to host Linux learning environment using Telegram bot as registration facility.



[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/tterb/atomic-design-ui/blob/master/LICENSEs)
  
## Rationale

ContainerSSH seemed like a **normal** way to solve the problem of hosting a platform for teaching Linux. 

My previous solution was a collection of hacks that kinda worked, 
but had lots of problems, like a lot of time to deploy
a single image, definitely some security issuess, no process management in containers...
You name it. And all of that using bash scripts. Definitely not worth publishing.

Unfortunately, ContainerSSH is not production-ready yet and does not have a sane default configuration. Here comes this repo. 
## Deployment

Enviromental variables to set. You should add them to `.env` file at the root of the project. 
```bash
BOT_TOKEN=HELLO_THIS_IS_TOKEN
ADMIN_ID=YOUR_NUMERIC_TELEGRAM_ID
```

Compose will source `.env` file before startup. Then just

```bash
  sudo docker-compose up -d
```
To actually run it (or without sudo if current user is in `docker` group) 

  
## Usage

MVP is here! Use template/Dockerfile.dummy[1-2] to test it!

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

- Easy-to-deploy public key authentication for docker socket, not an abysmal 100-something lines of bash copypasta. [CFSSL](https://github.com/cloudflare/cfssl), maybe?

- Bot's UI improvement: fix obvious bugs and typos, add text menu for image picking (easier for lots of images)

- Tests for bot

- Dockerfile template for image to deploy by containerssh (phusion+containerssh\_agent+checker template)

- Sane, secure default config

- Bind mounting user's directory as /home/student to preserve between launches

- Build and push images using Github Actions to speed up deployment

## Features

- Small disk footprint (distroless as base images for services)

- One command deploy.

- Template optimized for learning scenarios and feels more like an actual machine than a container.

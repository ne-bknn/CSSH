My setup to host a Linux learning environment for lots of people.

### Current state of ContainerSSH
1. No production-ready configuration provided
2. Authentication server needs to be created. Like, by yourself.
3. Public key auth in docker socket is not so easy.
4. I still do not get how to introduce several kinds of containers to drop people into.

### My solutions
`key_gen.sh` - silly script (more like a copypasta from https://docs.docker.com/engine/security/protect-access/) to generate keychain and setup docker to use TLS

`authconfig` - authentication microservice written in Go, public key only

`bot` - telegram bot to actually sign up and get a key.

So, on registration, bot generates keys and sends private one to the user, saving public one in Redis storage. On ssh login ContainerSSH asks auth service to validate the key. Seems like something doable.

### Setup overview

1. User registers with telegram bot; gets password, chooses task. Task is stored in redis.
2. On ssh connect cssh  verifies credentials over redis, fetches current task over redis. Success.

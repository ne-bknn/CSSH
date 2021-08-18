package main

import (
	"context"
	goHttp "net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"

	dockerContainer "github.com/docker/docker/api/types/container"

	golog "log"

	"github.com/containerssh/auth"
	"github.com/containerssh/configuration/v2"
	"github.com/containerssh/http"
	"github.com/containerssh/log"
	"github.com/containerssh/service"
	"github.com/go-redis/redis/v8"
)

type authHandler struct {
}

type DB struct {
	conn *redis.Client
}

func (d *DB) init() {
	redisAddr := os.Getenv("DB_HOST")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}

	rdb := redis.NewClient(&redis.Options{
		Addr:     redisAddr,
		Password: "",
		DB:       0,
	})

	d.conn = rdb
}

func (d *DB) get_id(Username string) (string, error) {
	var idKey strings.Builder
	idKey.WriteString("username:")
	idKey.WriteString(Username)

	id, err := d.conn.Get(ctx, idKey.String()).Result()

	return id, err
}

func (d *DB) get_password(Id string) (string, error) {
	var rdKey strings.Builder
	rdKey.WriteString("secrets:")
	rdKey.WriteString(Id)

	val, err := d.conn.Get(ctx, rdKey.String()).Result()

	return val, err
}

var ctx = context.Background()

func (a *authHandler) OnPassword(Username string, Password []byte, RemoteAddress string, ConnectionID string) (
	bool,
	error,
) {
	rdb := DB{}
	rdb.init()

	id, err := rdb.get_id(Username)

	if err == redis.Nil {
		golog.Printf("User %s does not exist\n", Username)
		return false, nil
	} else if err != nil {
		golog.Printf("Error getting ID from redis for user %s\n", Username)
		return false, nil
	}

	val, err := rdb.get_password(id)

	if err == redis.Nil {
		golog.Printf("User %s does not have a password, that should not happen", id)
		return false, nil
	} else if err != nil {
		golog.Printf("Error fetching from redis: %s\n", err)
		return false, nil
	}

	if val == string(Password) {
		golog.Printf("Successful login by user %s\n", Username)
		return true, nil
	}

	golog.Printf("Auth failed by user %s\n", Username)

	return false, nil
}

func (a *authHandler) OnPubKey(_ string, _ string, _ string, _ string) (
	bool,
	error,
) {
	return false, nil
}

type configHandler struct {
}

func (c *configHandler) OnConfig(request configuration.ConfigRequest) (configuration.AppConfig, error) {
	containerConfig := dockerContainer.Config{}
	config := configuration.AppConfig{}

	config.Backend = "docker"
	config.Docker.Connection.Host = "unix:///var/run/docker.sock"
	config.Docker.Execution.Launch.ContainerConfig = &containerConfig

	redisAddr := os.Getenv("DB_HOST")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}

	rdb := redis.NewClient(&redis.Options{
		Addr:     redisAddr,
		Password: "",
		DB:       0,
	})

	var idKey strings.Builder
	var Username = request.Username
	idKey.WriteString("username:")
	idKey.WriteString(Username)

	id, err := rdb.Get(ctx, idKey.String()).Result()

	if err == redis.Nil {
		golog.Printf("OnConfig: User %s does not exist\n", Username)
	} else if err != nil {
		golog.Printf("OnConfig: Error getting ID from redis for user %s\n", Username)
		return config, nil
	}

	var imageKey strings.Builder
	imageKey.WriteString("images:")
	imageKey.WriteString(id)

	imageName, err := rdb.Get(ctx, imageKey.String()).Result()

	if err != nil {
		golog.Printf("Error fetching config from redis, defaulting to bash")
		containerConfig.Image = "bash"
		golog.Printf("config.Docker.Execution.Launch.ContainerConfig.Image: %s\n", config.Docker.Execution.Launch.ContainerConfig.Image)
		return config, nil
	}

	containerConfig.Image = imageName

	golog.Printf("config.Docker.Execution.Launch.ContainerConfig.Image: %s\n", config.Docker.Execution.Launch.ContainerConfig.Image)
	return config, nil
}

type handler struct {
	auth   goHttp.Handler
	config goHttp.Handler
}

func (h *handler) ServeHTTP(writer goHttp.ResponseWriter, request *goHttp.Request) {
	switch request.URL.Path {
	case "/password":
		fallthrough
	case "/pubkey":
		h.auth.ServeHTTP(writer, request)
	case "/config":
		h.config.ServeHTTP(writer, request)
	default:
		writer.WriteHeader(404)
	}
}

func main() {
	logger, err := log.NewLogger(log.Config{
		Level:       log.LevelDebug,
		Format:      log.FormatLJSON,
		Destination: log.DestinationStdout,
	})

	if err != nil {
		panic(err)
	}

	authHTTPHandler := auth.NewHandler(&authHandler{}, logger)
	configHTTPHandler, err := configuration.NewHandler(&configHandler{}, logger)
	if err != nil {
		panic(err)
	}

	srv, err := http.NewServer(
		"authConfig",
		http.ServerConfiguration{
			Listen: "0.0.0.0:6823",
		},
		&handler{
			auth:   authHTTPHandler,
			config: configHTTPHandler,
		},
		logger,
		func(s string) {

		},
	)
	if err != nil {
		panic(err)
	}

	running := make(chan struct{})
	stopped := make(chan struct{})
	lifecycle := service.NewLifecycle(srv)
	lifecycle.OnRunning(
		func(s service.Service, l service.Lifecycle) {
			println("Auth-Config Server is now running...")
			close(running)
		}).OnStopped(
		func(s service.Service, l service.Lifecycle) {
			close(stopped)
		})
	exitSignalList := []os.Signal{os.Interrupt, os.Kill, syscall.SIGINT, syscall.SIGTERM}
	exitSignals := make(chan os.Signal, 1)
	signal.Notify(exitSignals, exitSignalList...)
	go func() {
		if err := lifecycle.Run(); err != nil {
			panic(err)
		}
	}()
	select {
	case <-running:
		if _, ok := <-exitSignals; ok {
			println("Stopping Test Auth-Config Server...")
			lifecycle.Stop(context.Background())
		}
	case <-stopped:
	}
}

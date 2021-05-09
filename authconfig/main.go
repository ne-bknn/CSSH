package main

import (
	"context"
	goHttp "net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"

	dockerContainer "github.com/docker/docker/api/types/container"

	"github.com/containerssh/auth"
	"github.com/containerssh/configuration"
	"github.com/containerssh/http"
	"github.com/containerssh/log"
	"github.com/containerssh/service"
	"github.com/go-redis/redis/v8"
	golog "log"
)

type authHandler struct {
}

var ctx = context.Background()

func (a *authHandler) OnPassword(Username string, Password []byte, RemoteAddress string, ConnectionID string) (
	bool,
	error,
) {
	if os.Getenv("TESTING") == "1" {
		return true, nil
	}

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
	idKey.WriteString("username:")
	idKey.WriteString(Username)

	id, err := rdb.Get(ctx, idKey.String()).Result()

	if err == redis.Nil {
		golog.Printf("User %s does not exist\n", Username)
	} else if err != nil {
		golog.Printf("Error getting ID from redis for user %s\n", Username)
		return false, nil
	}

	var rdKey strings.Builder
	rdKey.WriteString("secrets:")
	rdKey.WriteString(id)

	val, err := rdb.Get(ctx, rdKey.String()).Result()

	if err == redis.Nil {
		golog.Printf("User %s does not have a password, that should not happen", id)
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

	config.Docker.Execution.Launch.ContainerConfig = &containerConfig
	config.DockerRun.Config.ContainerConfig = &containerConfig

	redisAddr := os.Getenv("DB_CONN")
	if redisAddr == "" {
		redisAddr = "redis://localhost/0"
	}

	rdb := redis.NewClient(&redis.Options{
		Addr:     redisAddr,
		Password: "",
		DB:       0,
	})

	var imageKey strings.Builder
	imageKey.WriteString("images:")
	imageKey.WriteString(request.Username)

	imageName, err := rdb.Get(ctx, imageKey.String()).Result()

	if err != nil {
		containerConfig.Image = "bash"
		return config, nil
	}

	containerConfig.Image = imageName

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

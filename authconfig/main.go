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

	// should fetch config from envs

	rdb := redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		Password: "",
		DB:       0,
	})

	var rdKey strings.Builder
	rdKey.WriteString("passwords:")
	rdKey.WriteString(Username)
	val, err := rdb.Get(ctx, rdKey.String()).Result()

	if err != nil {
		return false, nil
	}

	if val == string(Password) {
		return true, nil
	}

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

	rdb := redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
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

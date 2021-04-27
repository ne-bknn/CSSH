package main

import (
	"context"
	"encoding/json"
	"io/ioutil"
	goHttp "net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/containerssh/auth"
	"github.com/containerssh/configuration"
	"github.com/containerssh/http"
	"github.com/containerssh/log"
	"github.com/containerssh/service"
)

type authHandler struct {
}

var imageNames []string

type Images struct {
	arr []string
}

func loadImageNames() {
	content, err := ioutil.ReadFile("images.json")
	if err != nil {
		panic(err)
	}

	err = json.Unmarshal([]byte(content), &imageNames)
	if err != nil {
		panic(err)
	}
}

func (a *authHandler) OnPassword(Username string, Password []byte, RemoteaAddress string, ConnectionID string) (
	bool,
	error,
) {
	if os.Getenv("TESTING") == "1" {
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

func stringInSlice(a string, list []string) bool {
    for _, b := range list {
        if b == a {
            return true
        }
    }
    return false
}

func (c *configHandler) OnConfig(request configuration.ConfigRequest) (configuration.AppConfig, error) {
	config := configuration.AppConfig{}

	if request.Username == "busybox" {
		config.Docker.Execution.Launch.ContainerConfig.Image = "busybox"
		config.DockerRun.Config.ContainerConfig.Image = "busybox"
	}

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
	loadImageNames()

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
		"authconfig",
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

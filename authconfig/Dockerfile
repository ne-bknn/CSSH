FROM golang:1.16-buster as build

WORKDIR /go/src/app
ADD go.mod go.sum ./

RUN go get -d -v ./...

ADD main.go ./

RUN go build -o /go/bin/authc

# Now copy it into our base image.
FROM gcr.io/distroless/base-debian10
COPY --from=build /go/bin/authc /
CMD ["/authc"]

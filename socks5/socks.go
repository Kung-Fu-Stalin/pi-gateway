package socks5

import (
	"context"
	"log"
	"net"
	"time"

	s5 "github.com/armon/go-socks5"
	"pi-gateway/config"
)

var server *s5.Server

type loggingDialer struct{}

func (d *loggingDialer) Dial(ctx context.Context, network, addr string) (net.Conn, error) {
	conn, err := (&net.Dialer{}).DialContext(ctx, network, addr)
	if err == nil {
		log.Printf("[SOCKS5] Connected to %s at %s\n", addr, time.Now().Format(time.RFC3339))
	}
	return conn, err
}

func StartSOCKS5() {
	conf := &s5.Config{
		AuthMethods: []s5.Authenticator{config.Auth},
		Dial:        (&loggingDialer{}).Dial,
	}

	var err error
	server, err = s5.New(conf)
	if err != nil {
		log.Fatal(err)
	}

	go func() {
		log.Println("SOCKS5 server listening on :1080")
		if err := server.ListenAndServe("tcp", "0.0.0.0:1080"); err != nil {
			log.Fatal(err)
		}
	}()
}

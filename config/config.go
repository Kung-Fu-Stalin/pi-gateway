package config

import (
	"log"
	"os"

	"github.com/armon/go-socks5"
	"gopkg.in/yaml.v2"
)

var Domains []string
var Auth *socks5.UserPassAuthenticator
var DDNS = "pigateway.duckdns.org:1080"

type Users struct {
	Users []struct {
		Username string `yaml:"username"`
		Password string `yaml:"password"`
	} `yaml:"users"`
}

func LoadDomains(path string) {
	data, err := os.ReadFile(path)
	if err != nil {
		log.Println("Failed to read domains.yaml:", err)
		return
	}
	var cfg struct{ Sites []string `yaml:"sites"` }
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		log.Println("Failed to parse domains.yaml:", err)
		return
	}
	Domains = cfg.Sites
	log.Println("Domains loaded")
}

func LoadUsers(path string) {
	data, err := os.ReadFile(path)
	if err != nil {
		log.Println("Failed to read users.yaml:", err)
		return
	}
	var users Users
	if err := yaml.Unmarshal(data, &users); err != nil {
		log.Println("Failed to parse users.yaml:", err)
		return
	}

	cred := socks5.StaticCredentials{}
	for _, u := range users.Users {
		cred[u.Username] = u.Password
	}

	Auth = &socks5.UserPassAuthenticator{Credentials: cred}
	log.Println("Users loaded")
}

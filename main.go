package main

import (
	"log"
	"net/http"

	"pi-gateway/config"
	"pi-gateway/pac"
	"pi-gateway/socks5"
	"pi-gateway/watcher"
)

func main() {
	config.LoadDomains("config/domains.yaml")
	config.LoadUsers("config/users.yaml")

	socks5.StartSOCKS5()

	http.HandleFunc("/family.pac", pac.PACHandler)
	go func() {
		log.Println("PAC server running at http://0.0.0.0:8080/family.pac")
		log.Fatal(http.ListenAndServe(":8080", nil))
	}()

	watcher.WatchFiles([]string{"config/domains.yaml", "config/users.yaml"})
}

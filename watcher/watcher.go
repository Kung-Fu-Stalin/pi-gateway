package watcher

import (
	"log"

	"gopkg.in/fsnotify.v1"
	"pi-gateway/config"
	"pi-gateway/pac"
)

func WatchFiles(files []string) {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		log.Fatal(err)
	}
	defer watcher.Close()

	for _, f := range files {
		if err := watcher.Add(f); err != nil {
			log.Fatal(err)
		}
	}

	for {
		select {
		case event := <-watcher.Events:
			if event.Op&fsnotify.Write == fsnotify.Write {
				switch event.Name {
				case "config/domains.yaml":
					config.LoadDomains(event.Name)
					pac.Regenerate()
				case "config/users.yaml":
					config.LoadUsers(event.Name)
				}
			}
		case err := <-watcher.Errors:
			log.Println("Watcher error:", err)
		}
	}
}

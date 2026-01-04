package pac

import (
	"bytes"
	"log"
	"net/http"
	"text/template"

	"pi-gateway/config"
)

var pacCache string
var pacTmpl *template.Template

func init() {
	var err error
	pacTmpl, err = template.ParseFiles("pac.tmpl")
	if err != nil {
		log.Fatal("Failed to parse PAC template:", err)
	}
	generatePAC()
}

func generatePAC() {
	data := config.Domains
	buf := &bytes.Buffer{}
	tmplData := struct {
		Sites []string
		DDNS  string
	}{
		Sites: data,
		DDNS:  config.DDNS,
	}

	if err := pacTmpl.Execute(buf, tmplData); err != nil {
		log.Println("Failed to execute PAC template:", err)
		return
	}

	pacCache = buf.String()
	log.Println("PAC regenerated")
}

func PACHandler(w http.ResponseWriter, r *http.Request) {
	if pacCache == "" {
		generatePAC()
	}
	w.Header().Set("Content-Type", "application/x-ns-proxy-autoconfig")
	w.Write([]byte(pacCache))
}

func Regenerate() {
	generatePAC()
}

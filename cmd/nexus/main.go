package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/osint-nexus/internal/engine"
	_ "go.uber.org/automaxprocs"
)

func run() error {
	if len(os.Args) < 2 {
		return fmt.Errorf("usage: nexus <username>")
	}
	username := os.Args[1]

	app, err := NewNexusApp()
	if err != nil {
		return fmt.Errorf("failed to initialize app: %w", err)
	}
	defer app.Close()

	fmt.Printf("Scanning for: %s\n", username)
	session, err := app.RunScan(context.Background(), username)
	if err != nil {
		return fmt.Errorf("failed to run scan: %w", err)
	}

	processSessionResults(app, session)
	return nil
}

func processSessionResults(app *NexusApp, session *engine.ScanSession) {
	for {
		select {
		case res, ok := <-session.ResultChan:
			if !ok {
				session.ResultChan = nil
			} else if res != nil {
				for _, acc := range res.Accounts {
					if acc.Username != nil && acc.Platform != nil {
						fmt.Printf("Found account: %s on %s\n", *acc.Username, *acc.Platform)
						if err := app.SaveResult(*acc.Username, *acc.Platform); err != nil {
							fmt.Fprintf(os.Stderr, "Error saving result: %v\n", err)
						}
					}
				}
			}
		case err, ok := <-session.ErrChan:
			if ok {
				fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			}
			session.ErrChan = nil
		}
		if session.ResultChan == nil && session.ErrChan == nil {
			break
		}
	}
}

func main() {
	if err := run(); err != nil {
		log.Printf("Error: %v\n", err)
		os.Exit(1)
	}
}

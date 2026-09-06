package main

import (
	"bufio"
	"context"
	"fmt"
	"log"
	"os"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/osint-nexus/internal/config"
	"github.com/osint-nexus/internal/engine"
	"github.com/osint-nexus/internal/ui"
	_ "go.uber.org/automaxprocs"
)

func run() error {
	var username string
	if len(os.Args) < 2 {
		var err error
		username, err = promptForUsername()
		if err != nil {
			return err
		}
	} else {
		username = os.Args[1]
	}

	app, err := NewNexusApp()
	if err != nil {
		return fmt.Errorf("failed to initialize app: %w", err)
	}
	defer app.Close()

	if len(os.Args) < 2 {
		return runDashboard(username)
	}

	fmt.Printf("Scanning for: %s\n", username)
	session, err := app.RunScan(context.Background(), username)
	if err != nil {
		return fmt.Errorf("failed to run scan: %w", err)
	}

	processSessionResults(app, session)
	return nil
}

func promptForUsername() (string, error) {
	reader := bufio.NewReader(os.Stdin)
	fmt.Print("Enter username: ")
	username, err := reader.ReadString('\n')
	if err != nil {
		return "", err
	}
	username = strings.TrimSpace(username)
	if username == "" {
		return "", fmt.Errorf("username cannot be empty")
	}
	return username, nil
}

func runDashboard(username string) error {
	p := tea.NewProgram(ui.NewModel(username))
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("failed to run dashboard: %w", err)
	}
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
	if _, err := config.LoadConfig(""); err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}
	if err := run(); err != nil {
		log.Printf("Error: %v\n", err)
		os.Exit(1)
	}
}

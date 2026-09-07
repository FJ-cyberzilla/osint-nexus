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
		return runDashboard(app, username)
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

func runDashboard(app *NexusApp, username string) error {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	session, err := app.RunScan(ctx, username)
	if err != nil {
		return fmt.Errorf("failed to start scan: %w", err)
	}

	p := tea.NewProgram(ui.NewModel(username))

	// Bridge session channels to Bubble Tea
	go func() {
		p.Send(ui.StatusMsg("Scan initiated..."))
		for {
			select {
			case <-ctx.Done():
				return
			case res, ok := <-session.ResultChan:
				if !ok {
					session.ResultChan = nil
				} else if res != nil {
					for _, acc := range res.Accounts {
						if acc.Platform != nil {
							p.Send(ui.ResultItem{
								Platform: *acc.Platform,
								Found:    true,
							})
						}
					}
					// Map relationships and shadows if present
					for _, edge := range res.Relationships.Edges {
						p.Send(ui.RelationMsg(fmt.Sprintf("%s -> %s (%s)", edge.Source, edge.Target, edge.RelationshipType)))
					}
				}
			case err, ok := <-session.ErrChan:
				if !ok {
					session.ErrChan = nil
				} else if err != nil {
					p.Send(ui.ErrorMsg(err.Error()))
				}
			case prog, ok := <-session.ProgressChan:
				if !ok {
					session.ProgressChan = nil
				} else {
					p.Send(ui.ProgressMsg(prog))
					if prog >= 1.0 {
						p.Send(ui.StatusMsg("Scan completed."))
					} else {
						p.Send(ui.StatusMsg(fmt.Sprintf("Scanning... %.0f%%", prog*100)))
					}
				}
			}

			if session.ResultChan == nil && session.ErrChan == nil && session.ProgressChan == nil {
				break
			}
		}
	}()

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

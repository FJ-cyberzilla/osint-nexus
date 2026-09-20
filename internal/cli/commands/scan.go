package commands

import (
	"context"
	"fmt"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/engine"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/FJ-cyberzilla/osint-nexus/pkg/osint"
	"github.com/rotisserie/eris"
	"github.com/spf13/cobra"
)

func init() {
	RootCmd.AddCommand(scanCmd)
}

var scanCmd = &cobra.Command{
	Use:   "scan [username]",
	Short: "Perform a comprehensive OSINT scan on a username",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		target := args[0]
		fmt.Printf("Starting scan for %s...\n", target)

		// Initialize orchestrator (defaulting to 5 concurrent providers)
		// Detector is nil for now as we just want to execute the scan
		orchestrator, err := engine.NewOrchestrator(5, nil)
		if err != nil {
			err = eris.Wrap(err, "cli: failed to create orchestrator")
			fmt.Printf("%s Error: %v\n", styleFailed.Render("✗"), err)
			return
		}

		agent, err := osint.NewAgent(target)
		if err != nil {
			err = eris.Wrap(err, "cli: failed to create agent")
			fmt.Printf("%s Error: %v\n", styleFailed.Render("✗"), err)
			return
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
		defer cancel()

		session, err := agent.RunScan(ctx, orchestrator, nil, time.Second*10)
		if err != nil {
			err = eris.Wrap(err, "cli: failed to run scan")
			fmt.Printf("%s Error: %v\n", styleFailed.Render("✗"), err)
			return
		}

		// Display results
		for res := range session.ResultChan {
			fmt.Printf("%s Profile found for username: %s\n", styleSuccess.Render("✓"), res.Username)
		}
		
		// Wait for errors
		for err := range session.ErrChan {
			if err != nil {
				fmt.Printf("%s Scan Error: %v\n", styleFailed.Render("✗"), err)
			}
		}

		fmt.Println("Scan completed.")
	},
}

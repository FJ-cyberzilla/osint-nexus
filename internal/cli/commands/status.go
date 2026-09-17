package commands

import (
	"fmt"

	"github.com/spf13/cobra"
)

func init() {
	RootCmd.AddCommand(statusCmd)
}

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Prints the status report",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println(styleTitle.Render("Nexus Status Report"))
		fmt.Printf("%s Build Engine\n", styleSuccess.Render("✓"))
		fmt.Printf("%s Linting\n", styleFailed.Render("✗"))
		fmt.Printf("%s Warning: Cache outdated\n", styleWarning.Render("!"))
		fmt.Printf("%s Tip: Use 'make build' to refresh\n", styleTip.Render("?"))
	},
}

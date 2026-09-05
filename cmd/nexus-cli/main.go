package main

import (
	"fmt"
	"os"

	"github.com/charmbracelet/lipgloss"
)

var (
	Version      = "1.0.0" // Set by linker
	styleTitle   = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("205")).MarginBottom(1)
	styleSuccess = lipgloss.NewStyle().Foreground(lipgloss.Color("46")).Bold(true)
	styleFailed  = lipgloss.NewStyle().Foreground(lipgloss.Color("196")).Bold(true)
	styleTip     = lipgloss.NewStyle().Foreground(lipgloss.Color("141")) // Light purple
	styleWarning = lipgloss.NewStyle().Foreground(lipgloss.Color("226")) // Yellow
	styleInfo    = lipgloss.NewStyle().Foreground(lipgloss.Color("86"))
)

func main() {
	if len(os.Args) < 2 {
		printAbout()
		return
	}

	switch os.Args[1] {
	case "version":
		fmt.Println(Version)
	case "about":
		printAbout()
	case "status":
		// Example of status output with checkmarks
		fmt.Println(styleTitle.Render("Nexus Status Report"))
		fmt.Printf("%s Build Engine\n", styleSuccess.Render("✓"))
		fmt.Printf("%s Linting\n", styleFailed.Render("✗"))
		fmt.Printf("%s Warning: Cache outdated\n", styleWarning.Render("!"))
		fmt.Printf("%s Tip: Use 'make build' to refresh\n", styleTip.Render("?"))
	default:
		fmt.Println("Unknown command")
	}
}

func printAbout() {
	fmt.Println(styleTitle.Render("OSINT-Nexus | Industrial Recon Engine"))
	fmt.Println(styleInfo.Render("A high-accuracy, low-level OSINT and network reconnaissance engine."))
	fmt.Printf("%s Version: %s\n", styleTip.Render("?"), Version)
}

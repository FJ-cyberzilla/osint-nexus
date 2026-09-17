package commands

import (
	"fmt"
	"os"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	cfgFile      string
	Version      = "1.0.0" // Set by linker
	styleTitle   = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("205")).MarginBottom(1)
	styleSuccess = lipgloss.NewStyle().Foreground(lipgloss.Color("46")).Bold(true)
	styleFailed  = lipgloss.NewStyle().Foreground(lipgloss.Color("196")).Bold(true)
	styleTip     = lipgloss.NewStyle().Foreground(lipgloss.Color("141")) // Light purple
	styleWarning = lipgloss.NewStyle().Foreground(lipgloss.Color("226")) // Yellow
	styleInfo    = lipgloss.NewStyle().Foreground(lipgloss.Color("86"))
)

// RootCmd represents the base command when called without any subcommands
var RootCmd = &cobra.Command{
	Use:   "nexus-cli",
	Short: "OSINT-Nexus | Industrial Recon Engine",
	Long:  `A high-accuracy, low-level OSINT and network reconnaissance engine.`,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		initConfig()
	},
	Run: func(cmd *cobra.Command, args []string) {
		printAbout()
	},
}

func init() {
	RootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is ./configs/config.yaml)")
}

func initConfig() {
	if cfgFile != "" {
		viper.SetConfigFile(cfgFile)
	} else {
		viper.AddConfigPath("./configs")
		viper.SetConfigName("config")
		viper.SetConfigType("yaml")
	}

	viper.AutomaticEnv()
	viper.SetEnvPrefix("NEXUS")
	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))

	if err := viper.ReadInConfig(); err == nil {
		fmt.Printf("Using config file: %s\n", viper.ConfigFileUsed())
	}
}

func printAbout() {
	fmt.Println(styleTitle.Render("OSINT-Nexus | Industrial Recon Engine"))
	fmt.Println(styleInfo.Render("A high-accuracy, low-level OSINT and network reconnaissance engine."))
	fmt.Printf("%s Version: %s\n", styleTip.Render("?"), Version)
}

func Execute() {
	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

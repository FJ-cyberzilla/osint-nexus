package commands

import (
	"fmt"
	"os"
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	cfgFile      string
	Version      = "1.0.0" 
	styleTitle   = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("205")).MarginBottom(1)
	styleSuccess = lipgloss.NewStyle().Foreground(lipgloss.Color("46")).Bold(true)
	styleFailed  = lipgloss.NewStyle().Foreground(lipgloss.Color("196")).Bold(true)
	styleWarning = lipgloss.NewStyle().Foreground(lipgloss.Color("226"))
	styleTip     = lipgloss.NewStyle().Foreground(lipgloss.Color("141")) 
	styleBox     = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("205")).
			Padding(1, 2)
)

// RootCmd represents the base command
var RootCmd = &cobra.Command{
	Use:   "nexus-cli",
	Short: "OSINT-Nexus | Industrial Recon Engine",
	Run: func(cmd *cobra.Command, args []string) {
		p := tea.NewProgram(initialDashboardModel())
		if _, err := p.Run(); err != nil {
			fmt.Printf("Error: %v\n", err)
			os.Exit(1)
		}
	},
}

type dashboardModel struct {
	textInput textinput.Model
	err       error
}

func initialDashboardModel() dashboardModel {
	ti := textinput.New()
	ti.Placeholder = "Enter target username..."
	ti.Focus()
	return dashboardModel{textInput: ti}
}

func (m dashboardModel) Init() tea.Cmd {
	return textinput.Blink
}

func (m dashboardModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.Type {
		case tea.KeyCtrlC, tea.KeyEsc:
			return m, tea.Quit
		case tea.KeyEnter:
			target := m.textInput.Value()
			if target == "" {
				return m, nil
			}
			// Switch to the actual dashboard UI with target
			return m, tea.Batch(tea.Quit) // Close input, then run scan in actual UI
		}
	}
	m.textInput, cmd = m.textInput.Update(msg)
	return m, cmd
}

func (m dashboardModel) View() string {
	return styleBox.Render(
		fmt.Sprintf("OSINT-Nexus | Command Center\n\n%s\n\n%s", 
			styleTitle.Render("Enter target username to begin reconnaissance:"),
			m.textInput.View()),
	) + "\n"
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

func Execute() {
	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

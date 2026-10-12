package commands

import (
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/FJ-cyberzilla/osint-nexus/internal/engine"
	"github.com/FJ-cyberzilla/osint-nexus/internal/ui"
	"github.com/FJ-cyberzilla/osint-nexus/pkg/osint"
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
		m, err := p.Run()
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			os.Exit(1)
		}
		
		// If a target was provided, launch the main UI
		if model, ok := m.(dashboardModel); ok && model.target != "" {
			launchDashboard(model.target)
		}
	},
}

type dashboardModel struct {
	textInput textinput.Model
	target    string
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
			m.target = target
			return m, tea.Quit 
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

func launchDashboard(target string) {
	model := ui.NewModel(target)
	p := tea.NewProgram(model, tea.WithAltScreen())

	go func() {
		orchestrator, err := engine.NewOrchestrator(5, nil)
		if err != nil {
			p.Send(ui.ErrorMsg(err.Error()))
			return
		}

		agent, err := osint.NewAgent(target)
		if err != nil {
			p.Send(ui.ErrorMsg(err.Error()))
			return
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
		defer cancel()

		p.Send(ui.StatusMsg("Starting OSINT reconnaissance..."))
		session, err := agent.RunScan(ctx, orchestrator, nil, time.Second*15)
		if err != nil {
			p.Send(ui.ErrorMsg(err.Error()))
			return
		}

		doneChan := make(chan struct{})
		go func() {
			defer close(doneChan)
			for prog := range session.ProgressChan {
				p.Send(ui.ProgressMsg(prog))
				p.Send(ui.StatusMsg(fmt.Sprintf("Scanning... (%.0f%%)", prog*100)))
			}
		}()

		go func() {
			for profile := range session.ResultChan {
				if profile != nil {
					for _, acc := range profile.Accounts {
						platform := "Unknown"
						if acc.Platform != nil {
							platform = *acc.Platform
						}
						p.Send(ui.ResultItem{
							Platform: platform,
							Found:    true,
						})
					}
					for _, email := range profile.Emails {
						p.Send(ui.EmailMsg(email))
					}
					for _, sm := range profile.SocialMedia {
						p.Send(ui.SocialMediaMsg(sm))
					}
				}
			}
		}()

		go func() {
			for scanErr := range session.ErrChan {
				if scanErr != nil {
					p.Send(ui.ErrorMsg(scanErr.Error()))
				}
			}
		}()

		<-doneChan
		p.Send(ui.StatusMsg("Scan completed."))
		p.Send(ui.ProgressMsg(1.0))
	}()

	if _, err := p.Run(); err != nil {
		fmt.Printf("Error launching dashboard: %v\n", err)
		os.Exit(1)
	}
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

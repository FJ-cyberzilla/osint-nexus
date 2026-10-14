package commands

import (
	"bytes"
	"testing"
)

func TestRootCommand(t *testing.T) {
	buf := new(bytes.Buffer)
	RootCmd.SetOut(buf)
	RootCmd.SetErr(buf)
	RootCmd.SetArgs([]string{"--help"})

	err := RootCmd.Execute()
	if err != nil {
		t.Fatalf("expected no error on --help, got %v", err)
	}

	output := buf.String()
	if output == "" {
		t.Fatalf("expected non-empty help output, got empty")
	}
}

func TestStatusCommand(t *testing.T) {
	buf := new(bytes.Buffer)
	statusCmd.SetOut(buf)
	statusCmd.SetErr(buf)
	
	// Test status run function
	if statusCmd.Run == nil {
		t.Fatalf("expected statusCmd.Run to be defined")
	}
	statusCmd.Run(statusCmd, []string{})
}

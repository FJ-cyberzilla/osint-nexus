package commands

import (
	"context"
	"fmt"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/detector"
	"github.com/rotisserie/eris"
	"github.com/spf13/cobra"
)

func init() {
	RootCmd.AddCommand(probeCmd)
	probeCmd.AddCommand(dnsCmd)
	probeCmd.AddCommand(tlsCmd)
	probeCmd.AddCommand(httpCmd)
	probeCmd.AddCommand(http2Cmd)
}

var probeCmd = &cobra.Command{
	Use:   "probe",
	Short: "Perform probes on a target",
}

var dnsCmd = &cobra.Command{
	Use:   "dns [hostname]",
	Short: "Perform a DNS probe on a target",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		target := args[0]
		fmt.Printf("Probing DNS %s...\n", target)
		d := detector.NewDNSDetector("8.8.8.8:53")
		ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
		defer cancel()

		result, err := d.Probe(ctx, target)
		if err != nil {
			err = eris.Wrap(err, "cli: dns probe failed")
			fmt.Printf("%s Error: %v\n", styleFailed.Render("✗"), err)
			return
		}
		fmt.Printf("%s DNS Probe Success\n", styleSuccess.Render("✓"))
		fmt.Printf("  %s %s\n", styleTip.Render("Resolver:"), result.Resolver)
		fmt.Printf("  %s %dms\n", styleTip.Render("Latency:"), result.Latency)
		fmt.Printf("  %s %v\n", styleTip.Render("Records:"), result.Records)
	},
}

var tlsCmd = &cobra.Command{
	Use:   "tls [address]",
	Short: "Perform a TLS probe on a target",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		target := args[0]
		fmt.Printf("Probing TLS %s...\n", target)
		d := detector.NewTLSDetector(time.Second * 5)
		ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
		defer cancel()

		result, err := d.Probe(ctx, target)
		if err != nil {
			err = eris.Wrap(err, "cli: tls probe failed")
			fmt.Printf("%s Error: %v\n", styleFailed.Render("✗"), err)
			return
		}
		fmt.Printf("%s TLS Probe Success\n", styleSuccess.Render("✓"))
		fmt.Printf("  %s %d\n", styleTip.Render("Version:"), result.Version)
		fmt.Printf("  %s %s\n", styleTip.Render("CipherSuite:"), result.CipherSuite)
		fmt.Printf("  %s %s\n", styleTip.Render("JA3:"), result.JA3)
	},
}

var httpCmd = &cobra.Command{
	Use:   "http [url]",
	Short: "Perform an HTTP probe on a target",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		target := args[0]
		fmt.Printf("Probing HTTP %s...\n", target)
		d := detector.NewHTTPDetector(time.Second * 5)
		ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
		defer cancel()

		result, err := d.Probe(ctx, target)
		if err != nil {
			err = eris.Wrap(err, "cli: http probe failed")
			fmt.Printf("%s Error: %v\n", styleFailed.Render("✗"), err)
			return
		}
		fmt.Printf("%s HTTP Probe Success\n", styleSuccess.Render("✓"))
		fmt.Printf("  %s %d\n", styleTip.Render("Status:"), result.StatusCode)
		fmt.Printf("  %s %dms\n", styleTip.Render("Latency:"), result.Latency)
		fmt.Printf("  %s %d headers found\n", styleTip.Render("Headers:"), len(result.Headers))
	},
}

var http2Cmd = &cobra.Command{
	Use:   "http2 [url]",
	Short: "Perform an HTTP/2 probe on a target",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		target := args[0]
		fmt.Printf("Probing HTTP/2 %s...\n", target)
		d := detector.NewHTTP2Detector(time.Second * 5)
		ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
		defer cancel()

		result, err := d.Probe(ctx, target)
		if err != nil {
			err = eris.Wrap(err, "cli: http2 probe failed")
			fmt.Printf("%s Error: %v\n", styleFailed.Render("✗"), err)
			return
		}
		fmt.Printf("%s HTTP/2 Probe Success\n", styleSuccess.Render("✓"))
		fmt.Printf("  %s %v\n", styleTip.Render("Supported:"), result.Supported)
		fmt.Printf("  %s %s\n", styleTip.Render("Protocol:"), result.Metadata["proto"])
	},
}

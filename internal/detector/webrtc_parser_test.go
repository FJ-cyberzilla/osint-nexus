package detector

import (
	"net"
	"testing"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/stretchr/testify/assert"
)

func TestParseIceCandidate(t *testing.T) {
	tests := []struct {
		name    string
		raw     string
		want    *types.IceCandidate
		wantErr bool
	}{
		{
			name: "Host candidate",
			raw:  "candidate:842163049 1 udp 1677721601 192.168.1.150 54321 typ host",
			want: &types.IceCandidate{
				Foundation: "842163049",
				Component:  1,
				Protocol:   "udp",
				Priority:   1677721601,
				Address:    net.ParseIP("192.168.1.150"),
				Port:       54321,
				Type:       types.CandidateHost,
			},
			wantErr: false,
		},
		{
			name: "Srflx candidate with raddr",
			raw:  "candidate:142385912 1 udp 2122260223 203.0.113.45 61234 typ srflx raddr 10.0.0.1 rport 54321",
			want: &types.IceCandidate{
				Foundation: "142385912",
				Component:  1,
				Protocol:   "udp",
				Priority:   2122260223,
				Address:    net.ParseIP("203.0.113.45"),
				Port:       61234,
				Type:       types.CandidateSrflx,
				RelAddr:    net.ParseIP("10.0.0.1"),
				RelPort:    54321,
			},
			wantErr: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ParseIceCandidate(tt.raw)
			if tt.wantErr {
				assert.Error(t, err)
				return
			}
			assert.NoError(t, err)
			assert.Equal(t, tt.want, got)
		})
	}
}

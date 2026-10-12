package detector

import (
	"net"

	"github.com/oschwald/maxminddb-golang"
	"github.com/rotisserie/eris"
)

// GeoData holds extracted city and country information.
type GeoData struct {
	Country string  `json:"country"`
	City    string  `json:"city"`
	Lat     float64 `json:"latitude"`
	Lon     float64 `json:"longitude"`
}

// MaxMind record mapping for GeoLite2-City
type mmdbCityRecord struct {
	City struct {
		Names map[string]string `maxminddb:"names"`
	} `maxminddb:"city"`
	Country struct {
		IsoCode string            `maxminddb:"iso_code"`
		Names   map[string]string `maxminddb:"names"`
	} `maxminddb:"country"`
	Location struct {
		Latitude  float64 `maxminddb:"latitude"`
		Longitude float64 `maxminddb:"longitude"`
	} `maxminddb:"location"`
}

// ASNData holds autonomous system details.
type ASNData struct {
	ASN          uint   `json:"asn"`
	Organization string `json:"organization"`
}

// MaxMind record mapping for GeoLite2-ASN
type mmdbASNRecord struct {
	AutonomousSystemNumber       uint   `maxminddb:"autonomous_system_number"`
	AutonomousSystemOrganization string `maxminddb:"autonomous_system_organization"`
}

// IPEnricher manages MMDB reader handles.
type IPEnricher struct {
	cityDB *maxminddb.Reader
	asnDB  *maxminddb.Reader
}

// NewIPEnricher initializes a new IPEnricher with the specified MMDB paths.
func NewIPEnricher(cityPath, asnPath string) (*IPEnricher, error) {
	cityDB, err := maxminddb.Open(cityPath)
	if err != nil {
		return nil, eris.Wrap(err, "detector: failed to open city mmdb")
	}

	asnDB, err := maxminddb.Open(asnPath)
	if err != nil {
		cityDB.Close()
		return nil, eris.Wrap(err, "detector: failed to open asn mmdb")
	}

	return &IPEnricher{
		cityDB: cityDB,
		asnDB:  asnDB,
	}, nil
}

// Close closes the underlying MMDB readers.
func (e *IPEnricher) Close() {
	if e.cityDB != nil {
		_ = e.cityDB.Close()
	}
	if e.asnDB != nil {
		_ = e.asnDB.Close()
	}
}

// LookupGeo returns location details for a given IP.
func (e *IPEnricher) LookupGeo(ip net.IP) (*GeoData, error) {
	var record mmdbCityRecord
	err := e.cityDB.Lookup(ip, &record)
	if err != nil {
		return nil, eris.Wrap(err, "detector: geo lookup failed")
	}

	return &GeoData{
		Country: record.Country.IsoCode,
		City:    record.City.Names["en"],
		Lat:     record.Location.Latitude,
		Lon:     record.Location.Longitude,
	}, nil
}

// LookupASN returns ASN details for a given IP.
func (e *IPEnricher) LookupASN(ip net.IP) (*ASNData, error) {
	var record mmdbASNRecord
	err := e.asnDB.Lookup(ip, &record)
	if err != nil {
		return nil, eris.Wrap(err, "detector: asn lookup failed")
	}

	return &ASNData{
		ASN:          record.AutonomousSystemNumber,
		Organization: record.AutonomousSystemOrganization,
	}, nil
}

package maxminddb

import "net"

type Reader struct{}

func Open(filename string) (*Reader, error) {
	return &Reader{}, nil
}

func (r *Reader) Close() error {
	return nil
}

func (r *Reader) Lookup(ip net.IP, result interface{}) error {
	return nil
}

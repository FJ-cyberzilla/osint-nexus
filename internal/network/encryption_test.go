package network

import (
	"bytes"
	"testing"
)

func TestEncryptionRoundtrip(t *testing.T) {
	key := make([]byte, 32)
	for i := range key {
		key[i] = byte(i)
	}

	plaintext := []byte("osint-nexus secure query payload")

	ciphertext, err := EncryptPayload(key, plaintext)
	if err != nil {
		t.Fatalf("Encryption failed: %v", err)
	}

	decrypted, err := DecryptPayload(key, ciphertext)
	if err != nil {
		t.Fatalf("Decryption failed: %v", err)
	}

	if !bytes.Equal(plaintext, decrypted) {
		t.Errorf("Decrypted payload does not match plaintext: got %s, want %s", string(decrypted), string(plaintext))
	}
}

func TestEncryptionInvalidKeySize(t *testing.T) {
	shortKey := []byte("short-key")
	_, err := EncryptPayload(shortKey, []byte("test"))
	if err == nil {
		t.Error("Expected error for short encryption key, got nil")
	}

	_, err = DecryptPayload(shortKey, []byte("test"))
	if err == nil {
		t.Error("Expected error for short decryption key, got nil")
	}
}

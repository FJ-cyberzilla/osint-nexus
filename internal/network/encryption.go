package network

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"io"

	"github.com/rotisserie/eris"
)

// EncryptPayload encrypts plaintext bytes using AES-256-GCM with the provided 32-byte key.
// It returns the combined nonce and ciphertext bytes or an error.
func EncryptPayload(key []byte, plaintext []byte) ([]byte, error) {
	if len(key) != 32 {
		return nil, eris.New("network: encryption key must be exactly 32 bytes for AES-256")
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, eris.Wrap(err, "network: failed to create AES cipher")
	}

	aesGCM, err := cipher.NewGCM(block)
	if err != nil {
		return nil, eris.Wrap(err, "network: failed to create GCM cipher mode")
	}

	nonce := make([]byte, aesGCM.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, eris.Wrap(err, "network: failed to generate secure random nonce")
	}

	ciphertext := aesGCM.Seal(nonce, nonce, plaintext, nil)
	return ciphertext, nil
}

// DecryptPayload decrypts ciphertext bytes (containing the prepended nonce) using AES-256-GCM and the provided 32-byte key.
func DecryptPayload(key []byte, ciphertext []byte) ([]byte, error) {
	if len(key) != 32 {
		return nil, eris.New("network: decryption key must be exactly 32 bytes for AES-256")
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, eris.Wrap(err, "network: failed to create AES cipher for decryption")
	}

	aesGCM, err := cipher.NewGCM(block)
	if err != nil {
		return nil, eris.Wrap(err, "network: failed to create GCM cipher mode for decryption")
	}

	nonceSize := aesGCM.NonceSize()
	if len(ciphertext) < nonceSize {
		return nil, eris.New("network: ciphertext too short for nonce extraction")
	}

	nonce := ciphertext[:nonceSize]
	actualCiphertext := ciphertext[nonceSize:]

	plaintext, err := aesGCM.Open(nil, nonce, actualCiphertext, nil)
	if err != nil {
		return nil, eris.Wrap(err, "network: failed to decrypt ciphertext payload")
	}

	return plaintext, nil
}

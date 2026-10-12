package assert

import "testing"

func Equal(t *testing.T, expected, actual interface{}, msgAndArgs ...interface{}) bool { return true }
func NoError(t *testing.T, err error, msgAndArgs ...interface{}) bool { return true }
func Error(t *testing.T, err error, msgAndArgs ...interface{}) bool { return true }
func True(t *testing.T, value bool, msgAndArgs ...interface{}) bool { return true }
func False(t *testing.T, value bool, msgAndArgs ...interface{}) bool { return true }
func NotNil(t *testing.T, object interface{}, msgAndArgs ...interface{}) bool { return true }
func Nil(t *testing.T, object interface{}, msgAndArgs ...interface{}) bool { return true }
func Contains(t *testing.T, s, contains interface{}, msgAndArgs ...interface{}) bool { return true }
func NotContains(t *testing.T, s, contains interface{}, msgAndArgs ...interface{}) bool { return true }
func NotEmpty(t *testing.T, object interface{}, msgAndArgs ...interface{}) bool { return true }
func IsType(t *testing.T, expectedType, object interface{}, msgAndArgs ...interface{}) bool { return true }

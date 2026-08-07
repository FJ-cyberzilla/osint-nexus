import sys

import mypy.api

sys.path.append(".")


def test_mypy_extractor():
    extractor_path = "osint_nexus/core/extractor.py"
    # Run mypy on this specific file
    stdout, stderr, exit_code = mypy.api.run([extractor_path, "--show-error-codes", "--strict"])

    if exit_code != 0:
        print(f"Mypy found errors in {extractor_path}:")
        print(stdout)
    else:
        print(f"No mypy errors in {extractor_path}")


if __name__ == "__main__":
    test_mypy_extractor()

import sys

import mypy.api

sys.path.append(".")


def test_mypy_browser_pool():
    pool_path = "osint_nexus/core/browser/pool.py"
    # Run mypy on this specific file
    stdout, stderr, exit_code = mypy.api.run(
        [
            pool_path,
            "--show-error-codes",
        ]
    )

    if exit_code != 0:
        print(f"Mypy found errors in {pool_path}:")
        print(stdout)
    else:
        print(f"No mypy errors in {pool_path}")


if __name__ == "__main__":
    test_mypy_browser_pool()

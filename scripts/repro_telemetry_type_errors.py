import sys

import mypy.api

sys.path.append(".")


def test_mypy_telemetry_bridge():
    bridge_path = "osint_nexus/core/telemetry/bridge.py"
    # Run mypy on this specific file
    stdout, stderr, exit_code = mypy.api.run(
        [
            bridge_path,
            "--show-error-codes",
            "--strict",  # Using strict to enforce better typing
        ]
    )

    if exit_code != 0:
        print(f"Mypy found errors in {bridge_path}:")
        print(stdout)
    else:
        print(f"No mypy errors in {bridge_path}")


if __name__ == "__main__":
    test_mypy_telemetry_bridge()

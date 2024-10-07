import sys

import pytest


def is_debug_mode():
    return sys.gettrace() is not None


def main():
    # Pytest arguments
    pytest_args = [
        "-s",  # Do not capture output, allowing you to see print statements and debug info
        "tests/unitary/yearn/test_rewards.py",  # Specific test to run
        # '--maxfail=1',  # Stop after the firstD failure
        "--tb=short",  # Shorter traceback for easier reading
        "-rA",  # Show extra test summary info
    ]

    if not is_debug_mode():
        pass
        pytest_args.append("-n=auto")  # Automatically determine the number of workers

    # Run pytest with the specified arguments
    pytest.main(pytest_args)


if __name__ == "__main__":
    main()

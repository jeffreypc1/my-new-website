"""
Per-file sys.modules isolation for API tests.

Each API test file adds its tool's app/ directory to sys.path and then
imports `app.*`. Because all tests run in one process, the `app` package
namespace would collide across tools. This conftest clears the cached
`app.*` entries before each test file is collected, allowing each file to
import its own `app` package cleanly.
"""

import sys


def pytest_collect_file(parent, file_path):
    """Clear cached app.* modules before every test file is collected."""
    if file_path.suffix == ".py" and file_path.name.startswith("test_"):
        for key in list(sys.modules.keys()):
            if key == "app" or key.startswith("app."):
                del sys.modules[key]
    return None

"""Clear cached app.* modules before test collection."""

import sys


def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".py" and file_path.name.startswith("test_"):
        for key in list(sys.modules.keys()):
            if key == "app" or key.startswith("app."):
                del sys.modules[key]
    return None

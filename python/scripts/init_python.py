#!/usr/bin/env python3
import importlib
import sys
import subprocess


required = {
    "numpy": "numpy",
    "cv2": "opencv-python",
    "pandas": "pandas",
    "pytest": "pytest",
    "toposort": "toposort",
    "dataclasses_json": "dataclasses_json",
}

for k, v in required.items():
    try:
        print(f"check module {k}")
        importlib.import_module(k)
    except ImportError:
        print(f"install module {k}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", v])
    finally:
        print(f"module {k} ok!")
        importlib.import_module(k)

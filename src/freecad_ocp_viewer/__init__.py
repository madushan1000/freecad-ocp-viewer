import subprocess
import traceback
import signal
import os
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("freecad_path", help="path to FreeCAD installation directory")
    parser.add_argument("main_file", help="build123d or cadquery file")
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    freecad_path = Path(args.freecad_path).resolve()
    main_file = args.main_file

    python_verson = f"{sys.version_info.major}.{sys.version_info.minor}"
    sys.path.append(str(freecad_path.joinpath(f"usr/lib/python{python_verson}/site-packages")))
    sys.path.append(str(freecad_path.joinpath("usr/lib")))

    os.environ["QT_QPA_PLATFORM"] = "xcb"
    os.environ["FONTCONFIG_FILE"] = str(freecad_path.joinpath("usr/etc/fonts/fonts.conf"))
    os.environ["FONTCONFIG_PATH"] = str(freecad_path.joinpath("usr/etc/fonts"))

    try:
        from .app import FreeCADOcpViewer
    except ModuleNotFoundError as e:
        print("\033[91mPlease make sure the FreeCAD path is correct, and you're using the same python verison FreeCAD is bundling.\033[0m")
        freecad_python_path =freecad_path.joinpath("usr/bin/python")
        if freecad_python_path.exists():
            freecad_python_version = subprocess.run(
                [freecad_python_path, "--version"],
                capture_output=True,
                text=True
            )
            print(f"\033[91mFreeCAD python version: {freecad_python_version.stdout.strip()}\033[0m")
            print(f"\033[91mYour python version: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\033[0m")

        raise e
    app = FreeCADOcpViewer(main_file, args.argv)
    app.setApplicationName("FreeCADOcpViewer")
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    return app.exec()

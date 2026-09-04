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

    sys.path.append(str(freecad_path.joinpath("usr/lib/python3.11/site-packages")))
    sys.path.append(str(freecad_path.joinpath("usr/lib")))

    os.environ["QT_QPA_PLATFORM"] = "xcb"
    os.environ["FONTCONFIG_FILE"] = str(freecad_path.joinpath("usr/etc/fonts/fonts.conf"))
    os.environ["FONTCONFIG_PATH"] = str(freecad_path.joinpath("usr/etc/fonts"))

    from .app import FreeCADOcpViewer
    app = FreeCADOcpViewer(main_file, args.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    return app.exec()

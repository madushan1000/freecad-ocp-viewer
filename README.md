# FreeCAD OCP Viewer

A small tool to visualize [CadQuery](https://github.com/cadquery/cadquery) or [buld123d](https://github.com/gumyr/build123d) projects in FreeCAD. This is not a FreeCAD workbench.

## Features

- Uses FreeCAD as the viewer.
- Automatic project hot reloading.

## How it works

The tool converts CadQuery or buld123d objects to OpenCASCADE BREP text format and imports them into FreeCAD as a FreeCAD shape.

It runs FreeCAD on the main thread via the `FreeCADGui` python API. And QFileSystemWatcher in a separate thread to monitor the CadQuery/build123d project you're editing to automatically hot reload it.

## Why

There are projects like [CQ-editor](https://github.com/CadQuery/CQ-editor), [vscode-ocp-cad-viewer](https://github.com/bernhard-42/vscode-ocp-cad-viewer) (which also has a standalone viewer independent of VSCode), and CadQuery's built-in VTK-based viewer.
But I didn't like any of them because they don't have some features I wanted, like convenient cross sections, good measurement tools, etc...

I came across [cadquery-freecad-workbench](https://github.com/CadQuery/cadquery-freecad-workbench), but it's difficult to install, only supports editing with the FreeCAD macro editor, and has no automatic hot reloading.

With FreeCAD OCP Viewer, I can use all of the FreeCAD tools I'm familiar with and use whatever editor I want with convenient automatic project hot reloading.


## Installation

### FreeCAD Appimage

Download the FreeCAD Appimage from [the website](https://www.freecad.org/downloads.php)

Unpack the Appimage

```bash
chmod +x ./FreeCAD-<version>.AppImage
./FreeCAD-<version>.AppImage --appimage-extract
mv squashfs-root freecad
```

### Install Python

Install [uv](https://docs.astral.sh/uv/).
The tool might work with other python package managers too. I did not test.

Find the python version FreeCAD was built with

```bash
$ ./freecad/usr/bin/python --version
Python 3.11.14
```

then,

```bash
mkdir <your project>
cd <your project>
uv venv
uv python pin <python version>
# eg: uv python pin 3.11.14
```

You can get a list of available versions to install by running `uv python list`

### Install FreeCAD OCP Viewer

```bash
uv pip install git+https://github.com/madushan1000/freecad-ocp-viewer
```

Make sure to install `cadquery` or `build123d`, whichever your project uses.

```bash
uv pip install cadquery build123d
```

## Usage

The tool argument format is `uv run freecad-ocp-viewer <freecad path> <main project file>`

```bash
uv run freecad-ocp-viewer <freecad path> <your main project file>
#eg: uv run freecad-ocp-viewer ../freecad main_part.py
```

You can use `show_object` function to view your object. It only supports passing one object along with a name. It doesn't support all the features of the CadQuery `show_object` function.

```python
show_object(obj, "obj_name")
```

## Notice

This tool is only tested on Linux with the FreeCAD AppImage.

It will probably not work on other platforms/packaging methods without some modification.
But the tool is not very complicated, so it should not be difficult to get it working with whatever environment you have.

The code is not very robust, excpect bugs.



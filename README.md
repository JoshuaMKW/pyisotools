# pyisotools
python library for working with Gamecube ISOs (GCM)

# Features
- Extract and Build ISOs
- Extract individual files/folders from an ISO
- Specifically exclude subfolders/files using glob patterns
- Custom file alignment
- Custom file location
- Custom ISO metadata

# Limitations
- Only supports Gamecube ISOs

# TODO
- Support Wii ISOs

# Usage

## GUI
To run the GUI from the cli, simply pass: `python -m pyisotools`

## Extraction
To extract an ISO from the cli, pass: `python -m pyisotools <iso> E [--dest path]`

## Rebuilding
To build a root folder into an iso, pass: `python -m pyisotools <root> B [--newinfo] [--dest path]`

## Configuration (rebuilding from cli)
When an ISO is extracted, a file named `.config.json` is automatically generated and stored in the `sys` folder in the root directory. This file contains metadata about the ISO, such as the name of the game, its version, maker code, and so on. Editing this file results in the new data being used if rebuilding with option `--newinfo` enabled. The fields that need clairification are listed below:

- Alignment: This field of `key,value` pairs defines the alignment of every file that matches the specified glob pattern set as the `key`, to be that of the `value`
- Location: This field of `key,value` pairs defines the position in the ISO of every file that matches the specified filepath set as the `key`, to be that of the `value`
- Exclude: This list of glob patterns determines if a file/folder is excluded or not. If a file/folder path matches any of the glob patterns in the list, it will not be built into the ISO

## Configuration (GUI)
When a root is loaded, all metadata fields are accessible directly from the main window, and each node can be right clicked on to set the alignment, location, and exclude members
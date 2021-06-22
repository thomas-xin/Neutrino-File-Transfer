# Neutrino-File-Transfer
A multithreaded file transfer program that recursively concatenates a folder of files. Intended for fast transfer of databases with thousands of small files, currently implemented to be uncompressed.

## Features
- `python neutrino.py input` will copy the file or folder `input` into a single file named `.output`.
- `python neutrino.py .output` (Note: currently hardcoded to be the string `".output"`) will extract all files in `.output` and place them in a folder named `output`.

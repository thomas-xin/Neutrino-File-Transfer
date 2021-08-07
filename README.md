# Neutrino-File-Transfer
A multithreaded file transfer program that recursively concatenates a folder of files. Has no limit on maximum filesize nor number of files (though if there are billions of files it may run out memory, and is obviously bounded by disk space/filesystem limits). Intended for fast transfer of databases with thousands of small files, currently implemented to be uncompressed. Originally designed for [Miza](https://github.com/thomas-xin/Miza)'s database.

## Features
- `python neutrino.py input` will copy the file or folder `input` into a single file named `.output`.
- `python neutrino.py .output` (Note: currently hardcoded to be the string `".output"`) will extract all files in `.output` and place them in a folder named `output`.
- Duplicate files are omitted and instead stored as pointers to their copies.
- The file metadata is stored at the end, and is read in reverse during restoration.
- Relative paths and their indices in the concatenated file are stored at the end of the output file and will be used to restore them.
- The file is terminated by a 0x80-separated little endian number representing the size in bytes of the file path object.

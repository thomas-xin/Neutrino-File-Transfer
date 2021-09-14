# Neutrino-File-Transfer
A multithreaded file transfer program that recursively concatenates a folder of files. Has no limit on maximum filesize nor number of files (though if there are billions of files it may run out of memory, and is obviously bounded by disk space/filesystem limits). Intended for fast transfer of databases with tens or hundreds of thousands of small files (or a smaller amount of larger files), currently implemented to be uncompressed. Originally designed for [Miza](https://github.com/thomas-xin/Miza)'s database.

## Features
- `python neutrino.py input output.wb` will copy the folder `input` into a single file named `.output.wb`, uncompressed.
- `python neutrino.py -c input output.wb` will copy the file `input` into a single file named `.output.wb`, compressed using DEFLATE.
- `python neutrino.py input.wb output` will extract all files in `input.wb` and place them in a folder named `output`.
- `python neutrino.py input.wb -f a/b.` will find and extract `a/b` from `input.wb`, and output its contents into stdout.


- Duplicate files are omitted and instead stored as pointers to their copies.
- The file metadata is stored at the end, and is read in reverse during restoration. The first file in the folder 
- Relative paths and their indices in the concatenated file are stored at the end of the output file and will be used to restore them.
- The file is terminated by a 0x80-separated little endian number representing the size in bytes of the file path object.
- Compression is currently done by the program invoking itself a second time, concatenating a folder of zip files.

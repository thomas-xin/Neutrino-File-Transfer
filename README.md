# Neutrino-File-Transfer
A multithreaded file transfer program that recursively concatenates a folder of files.
Has no limit on maximum filesize nor number of files (though if there are billions of files it may run out of memory, and is obviously bounded by disk space/filesystem limits).
Intended for easy packing and fast transfer of databases with tens or hundreds of thousands of small files (or a smaller amount of larger files).
Originally designed for [Miza](https://github.com/thomas-xin/Miza)'s database.

Functions very similarly to `.zip`, `.tar` and `.tar.gz` files, being a file format that can contain multiple other files, potentially in a compressed encoding.
The advantages of this program itself, is that it uses multiple processes and threads (maximum 34 total processes and 226 threads) in order to greatly speed up both the encoding and decoding process, which makes a difference when there is a massive amount of data that needs to be processed.
The file format itself also supports concurrency better than other compression formats.
Having more CPU cores and/or an SSD will allow this program to reach much higher efficiency potential.
The compression feature itself uses [4x4](https://www.sac.sk/files.php?d=7&l=4) as the backend. Note that this is a 32-bit program, meaning on 64-bit operating systems, 32-bit support will need to be installed.
## Features
- `python neutrino.py input` will copy the folder `input` into a single file named `input.wb`, uncompressed.
- `python neutrino.py input output.wb` will copy the folder `input` into a single file named `output.wb`, uncompressed.
- `python neutrino.py -c input output.wb` will copy the file `input` into a single file named `output.wb`, compressed with level 5.
- `python neutrino.py -c9 -y input` will copy the file `input` into a single file named `input.wb`, compressed with level 9. Will ignore and replace the target file if it already exists, instead of creating a new one under a unique name.
- `python neutrino.py input.wb output` will extract all files in `input.wb` and place them in a folder named `output`.
- `python neutrino.py input.wb -f a/b.` will find and extract `a/b` from `input.wb`, and output its contents into stdout.


- Duplicate files are omitted and instead stored as pointers to their copies.
- The file metadata is stored at the end, and is read in reverse during restoration.
The first file in the folder will be stored at the front of the file, and if using uncompressed mode, may even be viewed as that file.
- Relative paths and their indices in the concatenated file are stored at the end of the output file and will be used to restore them.
- The file is terminated by a 0x80-separated little endian number representing the size in bytes of the file path object. This is read first during extraction.
- Compression is currently implemented as the program invoking `4x4` as a subprocess to perform the operation on the resulting file.
- Compression level is specified by the flag `-c{x}`, where `{x}` is an integer from 0 to 9. 0 provides no compression, 1\~4 use LZ77-Huffman (similar to .zip files) compression with improved speed, whereas 5\~9 use LZMA (similar to .7z files) for improved compress ratio. Level 3 is sufficient to beat typical `.zip` files, while level 6 is sufficient to beat `.7z` files. For most intents and purposes it is advised to use a value between these two in order to prevent potentially useless or unbearably slow processing.

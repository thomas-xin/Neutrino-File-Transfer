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
### Flags
- `-c{x}` where `{x}` is an integer from 0 to 9, such as `-c7`. The levels are sorted in increments of compression efficiency, with 0 providing no compression, 1\~4 using LZ77-Huffman (similar to .zip files) compression with improved speed, whereas 5\~9 use LZMA (similar to .7z files) for improved compress ratio. Level 3 is sufficient to beat typical `.zip` files, while level 6 outmatches `.7z` files. For most intents and purposes it is advised to use a value somewhere around these two in order to prevent potentially useless or unbearably slow processing.
- `-y` forces overwrite of target file if it already exists, instead of creating a new file under a new name.
- `-e` forces encode mode, even if the input is a single file (by default the program only encodes folders)
- `-f "folder/file"` reads "folder/file" from the input, outputting contents to stdout, with all other outputs being suppressed. Useful if you're wanting to extract only a single file and read it directly, invoking the program as a standalone API.
- `--encrypt "password here"` will encrypt the output using password `password here`. The currently employed encryption method is EmojiCrypt, a custom algorithm that will shuffle the input data's bytes, before applying an addition operation, encoding it in b85, and then feeding it through a shuffled emoji translator, outputting a mess of unicode smileys. This is a very inefficient storage format, as it uses 5x the amount of space as the compressed input, and is mostly included for novelty purposes. It is nevertheless a fairly secure algorithm, as it is seeded with SHA-512 and PCG-64.
- `--decrypt "password here"` the opposite of `--encrypt` above; the emoji scrambler is fully reversible provided the correct password is used.
### Examples
- `python neutrino.py input` will copy the folder `input` into a single file named `input.wb`, uncompressed.
- `python neutrino.py input output.wb` will copy the folder `input` into a single file named `output.wb`, uncompressed.
- `python neutrino.py -c9 -y input` will copy the file `input` into a single file named `input.wb`, compressed with level 9. Will ignore and replace the target file if it already exists, instead of creating a new one under a unique name.
- `python neutrino.py -c7 -e input.txt output.wb` will copy the single file `input.txt` into a single file named `output.wb`, compressed with level 7.
- `python neutrino.py -c --encrypt "password here" input output.wb` will copy the folder or file `input` into a single file named `output.wb`, compressed with level 5, then encrypted using the password "password here".

- `python neutrino.py input.wb output` will extract all files in `input.wb` and place them in a file or folder named `output`.
- `python neutrino.py --decrypt "password here" input.wb output` will extract all files in `input.wb` and place them in a file or folder named `output`, decrypting using password "password here".
- `python neutrino.py input.wb -f a/b.` will find and extract `a/b` from `input.wb`, and output its contents into stdout.


- Duplicate files are omitted and instead stored as pointers to their copies.
- The file metadata is stored at the end, and is read in reverse during restoration.
The first file in the folder will be stored at the front of the file, and if using uncompressed mode, may even be viewed as that file.
- Relative paths and their indices in the concatenated file are stored at the end of the output file and will be used to restore them.
- The file is terminated by a 0x80-separated little endian number representing the size in bytes of the file path object. This is read first during extraction.
- Compression is currently implemented as the program invoking `4x4` as a subprocess to perform the operation on the resulting file.
- If compression would leave the output larger than the input, the compression step will be skipped.
- If speed is desired more than compression, it may be advised to drop the compression altogether and run the program with -c0 (or without the -c flag at all), as any level of compression (even level 1) will reduce the speed of the program by at least half, becoming exponentially worse with higher levels. Thus, it can be much more efficient for file transferring to simply leave the file uncompressed, as the standalone concatenation can be so much faster.

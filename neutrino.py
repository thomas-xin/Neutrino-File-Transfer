import os


def copyfileobj(fsrc, fdst, length=1048576, size=None):
    pos = 0
    while True:
        if size is not None:
            bufsize = min(length, size - pos)
        else:
            bufsize = length
        buf = fsrc.read(bufsize)
        if not buf:
            break
        pos += len(buf)
        fdst.write(buf)

def write_into(out, i, pos):
    with open(out, "rb+") as fo:
        if pos:
            fo.seek(pos)
        with open(i, "rb") as fi:
            copyfileobj(fi, fo)

def read_into(out, argv, i, pos, size):
    with open(os.path.join(out, i), "wb") as fo:
        with open(argv, "rb") as fi:
            fi.seek(pos)
            copyfileobj(fi, fo, size=size)

def filecmp(fsrc, fdst, length=1048576):
    while True:
        fut = submit(fsrc.read, length)
        y = fdst.read(length)
        x = fut.result()
        if x != y:
            return
        if not x:
            return True


if __name__ == "__main__":
    import sys, time, collections, pickle, io, zipfile, concurrent.futures, subprocess
    from concurrent.futures import thread
    from collections import deque

    def _adjust_thread_count(self):
        # if idle threads are available, don't spin new threads
        try:
            if self._idle_semaphore.acquire(timeout=0):
                return
        except AttributeError:
            pass

        # When the executor gets lost, the weakref callback will wake up
        # the worker threads.
        def weakref_cb(_, q=self._work_queue):
            q.put(None)

        num_threads = len(self._threads)
        if num_threads < self._max_workers:
            thread_name = '%s_%d' % (self._thread_name_prefix or self, num_threads)
            t = thread.threading.Thread(
                name=thread_name,
                target=thread._worker,
                args=(
                    thread.weakref.ref(self, weakref_cb),
                    self._work_queue,
                    self._initializer,
                    self._initargs,
                ),
                daemon=True
            )
            t.start()
            self._threads.add(t)
            thread._threads_queues[t] = self._work_queue

    concurrent.futures.ThreadPoolExecutor._adjust_thread_count = lambda self: _adjust_thread_count(self)

    ppe = concurrent.futures.ProcessPoolExecutor(max_workers=32)
    tpe = concurrent.futures.ThreadPoolExecutor(max_workers=192)
    submit = tpe.submit

    argv = sys.argv[1] if len(sys.argv) > 1 else None

    while not argv:
        argv = input("Please enter file or folder to process: ")

    if os.path.isdir(argv):
        out = sys.argv[2] if len(sys.argv) > 2 else ".output"
        info = deque((deque(),))
        names = {}
        sizes = {}
        hashes = {}
        extras = deque()

        hsize = 16384

        def _get_hash(path, pos):
            with open(path, "rb") as f:
                f.seek(pos)
                return f.read()

        def get_hash(path=".", size=0):
            if size > hsize:
                pos = max(hsize, size - hsize)
                fut = submit(_get_hash, path, pos)
                y = True
            else:
                y = False
            with open(path, "rb") as f:
                x = f.read(hsize)
            if y:
                return hash(x) + hash(fut.result()) + size
            return hash(x) + size

        def recursive_scan(path=".", pos=0):
            files = deque()
            for f in os.scandir(path):
                if f.is_file(follow_symlinks=False):
                    s = f.stat()
                    size = s.st_size
                    if size:
                        if size in sizes:
                            h = get_hash(f.path, size=size)
                            try:
                                for f2 in sizes[size]:
                                    try:
                                        h2 = hashes[f2]
                                    except KeyError:
                                        h2 = hashes[f2] = get_hash(f2, size=size)
                                    if h == h2:
                                        with open(f.path, "rb") as fi:
                                            with open(f2, "rb") as fo:
                                                if filecmp(fi, fo):
                                                    extras.append((os.path.relpath(f.path, argv), names[f2], size))
                                                    raise StopIteration
                            except StopIteration:
                                continue
                            hashes[f.path] = h
                        files.append(f.path)
                        info.append((os.path.relpath(f.path, argv), pos, size))
                        names[f.path] = pos
                        try:
                            sizes[size].append(f.path)
                        except KeyError:
                            sizes[size] = deque((f.path,))
                        pos += size
                    else:
                        extras.append((os.path.relpath(f.path, argv), 0, 0))
                elif f.is_dir(follow_symlinks=False):
                    fp = os.path.relpath(f.path, argv)
                    info[0].append(fp)
                    sub, pos = recursive_scan(path=f.path, pos=pos)
                    files.extend(sub)
                    pos = pos
            return files, pos

        sys.stdout.write("Scanning...")

        fut = submit(recursive_scan, argv)
        count = 0
        while not fut.done():
            count2 = len(info) - 1 + len(extras)
            if count < count2:
                count = count2
                sys.stdout.write(f"\rScanning ({count})...")
                time.sleep(0.03)
        print(f"\rScanned ({len(info) - 1 + len(extras)}).   ")

        files, pos = fut.result()
        info.extend(extras)

        fs = pos
        infodata = pickle.dumps(info)
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=False) as z:
            z.writestr("M", infodata)
        b.seek(0)
        infodata = b.read()
        infolen = len(infodata).to_bytes(len(infodata).bit_length() + 7 >> 3, "little")
        infodata += b"\x80" * 2 + b"\x80".join(bytes((i,)) for i in infolen)
        fs += len(infodata)

        t = time.time()

        if os.name == "nt":
            if os.path.exists(out):
                os.remove(out)
            subprocess.run(("fsutil", "file", "createnew", out, f"{fs}"))
        else:
            subprocess.run(f"truncate -s {fs} {out}", shell=True)

        futs = deque()
        pfuts = deque()
        indices = sorted(range(len(files)), key=lambda i: info[i + 1][2])
        quarter = len(indices) >> 2
        for f in map(files.__getitem__, reversed(indices[-quarter:])):
            pfuts.appendleft(ppe.submit(write_into, out, f, names[f]))
        for f in map(files.__getitem__, indices[:-quarter]):
            futs.append(submit(write_into, out, f, names[f]))
        futs.extend(pfuts)
        for i, fut in enumerate(futs):
            try:
                fut.result()
                sys.stdout.write(f"\r{i}/{len(futs)}")
            except FileNotFoundError:
                pass
        sys.stdout.write(f"\r{len(futs)}/{len(futs)}\n")

        with open(out, "rb+") as f:
            f.seek(fs - len(infodata))
            f.write(infodata)

        print(f"{fs} bytes written in {round(time.time() - t, 4)} seconds; {len(files)} unique files/folders, {len(extras)} duplicate/empty files.")

    else:
        out = sys.argv[2] if len(sys.argv) > 2 else "output"
        fs = os.path.getsize(argv)
        infolen = b""

        sys.stdout.write("Scanning...")

        with open(argv, "rb") as f:
            b = c = b""
            for i in range(fs - 1, -1, -1):
                f.seek(i)
                b = c
                c = f.read(1)
                if b == c == b"\x80":
                    break
                infolen = c + infolen
            infolen = int.from_bytes(infolen[1::2], "little")
            i -= infolen
            f.seek(i)
            infodata = f.read(infolen)
        b = io.BytesIO(infodata)
        with zipfile.ZipFile(b, "r") as z:
            infodata = z.read("M")
        info = pickle.loads(infodata)

        print(f"\rScanned ({len(info) - 1 + len(info[0])}).   ")

        fs = 0
        t = time.time()
        filec = extrac = 0

        if not os.path.exists(out):
            os.mkdir(out)
        for f in sorted(info[0], key=len):
            fn = os.path.join(out, f)
            try:
                os.mkdir(fn)
            except FileExistsError:
                extrac += 1
            else:
                filec += 1
        info.popleft()

        futs = deque()
        pfuts = deque()
        tuples = sorted(info, key=lambda t: t[2])
        quarter = len(tuples) >> 2
        for path, pos, size in reversed(tuples[-quarter:]):
            if not size:
                with open(os.path.join(out, argv), "wb") as fo:
                    extrac += 1
            else:
                pfuts.appendleft(ppe.submit(read_into, out, argv, path, pos, size))
                filec += 1
                fs += size
        for path, pos, size in tuples[:-quarter]:
            if not size:
                with open(os.path.join(out, argv), "wb") as fo:
                    extrac += 1
            else:
                futs.append(submit(read_into, out, argv, path, pos, size))
                filec += 1
                fs += size
        futs.extend(pfuts)
        for i, fut in enumerate(futs):
            fut.result()
            sys.stdout.write(f"\r{i}/{len(futs)}")
        sys.stdout.write(f"\r{len(futs)}/{len(futs)}\n")

        print(f"{fs} bytes written in {round(time.time() - t, 4)} seconds; {filec} valid files/folders, {extrac} empty files.")

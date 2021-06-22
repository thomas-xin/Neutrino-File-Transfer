import os, sys, collections, pickle, zipfile, concurrent.futures, subprocess

from concurrent.futures import thread
from collections import deque

def _adjust_thread_count(self):
    # if idle threads are available, don't spin new threads
    if self._idle_semaphore.acquire(timeout=0):
        return

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

exc = concurrent.futures.ThreadPoolExecutor(max_workers=512)
submit = exc.submit

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


argv = " ".join(sys.argv[1:]) or "."

if argv != ".output":
    out = ".output"
    info = deque((deque(),))
    names = {}

    def recursive_scan(path=".", pos=0):
        files = deque()
        for f in os.scandir(path):
            if f.is_file(follow_symlinks=False):
                s = f.stat()
                if s.st_size:
                    files.append(f.path)
                    info.append((os.path.relpath(f.path, argv), pos, s.st_size))
                    names[f.path] = pos
                    pos += s.st_size
            elif f.is_dir(follow_symlinks=False):
                fp = os.path.relpath(f.path, argv)
                info[0].append(fp)
                sub, pos = recursive_scan(path=f.path, pos=pos)
                files.extend(sub)
                pos = pos
        return files, pos

    files, pos = recursive_scan(argv)

    fs = pos
    infodata = pickle.dumps(info)
    infolen = len(infodata).to_bytes(len(infodata).bit_length() + 7 >> 3, "little")
    infodata += b"\x80" * 2 + b"\x80".join(bytes((i,)) for i in infolen)
    fs += len(infodata)

    if os.name == "nt":
        if os.path.exists(out):
            os.remove(out)
        subprocess.run(("fsutil", "file", "createnew", out, f"{fs}"))
    else:
        subprocess.run(f"truncate -s {fs} {out}", shell=True)

    def write_into(i):
        with open(out, "rb+") as fo:
            if names.get(i):
                fo.seek(names[i])
            with open(i, "rb") as fi:
                copyfileobj(fi, fo)

    futs = deque()
    for f in files:
        futs.append(submit(write_into, f))
    for i, fut in enumerate(futs):
        fut.result()
        sys.stdout.write(f"\r{i}/{len(futs)}")
    sys.stdout.write(f"\r{len(futs)}/{len(futs)}\n")

    with open(out, "rb+") as f:
        f.seek(fs - len(infodata))
        f.write(infodata)

    print(f"{fs} bytes written.")

else:
    out = "output"
    fs = os.path.getsize(argv)
    infolen = b""
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
    info = pickle.loads(infodata)
    if not os.path.exists(out):
        os.mkdir(out)
    for f in sorted(info[0], key=len):
        fn = os.path.join(out, f)
        try:
            os.mkdir(fn)
        except FileExistsError:
            pass
    info.popleft()

    def read_into(i, pos, size):
        with open(os.path.join(out, i), "wb") as fo:
            with open(argv, "rb") as fi:
                fi.seek(pos)
                copyfileobj(fi, fo, size=size)

    futs = deque()
    for path, pos, size in info:
        futs.append(submit(read_into, path, pos, size))
    for i, fut in enumerate(futs):
        fut.result()
        sys.stdout.write(f"\r{i}/{len(futs)}")
    sys.stdout.write(f"\r{len(futs)}/{len(futs)}\n")
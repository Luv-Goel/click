import click
import os
import pytest
import tempfile
import threading


def test_iter_lazyfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        with click.utils._LazyFile(f.name) as lf:
            for e_line, a_line in zip(expected, lf, strict=False):
                assert e_line == a_line.strip()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="fifos are not supported on this platform")
def test_lazy_file_does_not_eagerly_open_fifo(tmp_path):
    # Regression test for #2645: a lazy file opened for reading must not
    # eagerly open+close a named pipe (fifo), which can drain or break it.
    fifo_path = tmp_path / "myfifo"
    os.mkfifo(fifo_path)
    payload = b"hello fifo\n"

    def writer():
        wfd = os.open(fifo_path, os.O_WRONLY)
        os.write(wfd, payload)
        os.close(wfd)

    t = threading.Thread(target=writer, daemon=True)
    t.start()

    lf = click.utils._LazyFile(fifo_path, "rb")
    assert lf.open().read() == payload
    lf.close()

    t.join(timeout=5)
    assert not t.is_alive()

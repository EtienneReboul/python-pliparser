import subprocess


def test_main():
    assert subprocess.check_output(["pliparser", "foo", "foobar"], text=True) == "foobar\n"

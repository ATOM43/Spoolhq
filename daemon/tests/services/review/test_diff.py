import re

from spoolhq.services.review import DIFF_MAX_CHARS, trim_diff


def file_diff(name: str, lines: int) -> str:
    header = (
        f"diff --git a/{name} b/{name}\nindex 0000000..1111111 100644\n--- a/{name}\n+++ b/{name}\n"
    )
    hunk = f"@@ -1,0 +1,{lines} @@\n" + "".join(f"+line {i} of {name}\n" for i in range(lines))
    return header + hunk


def test_small_diff_is_unchanged() -> None:
    diff = file_diff("a.py", 3)
    assert trim_diff(diff) == (diff, False)


def test_large_diff_keeps_every_header_and_whole_files() -> None:
    names = [f"src/module_{i:02}.py" for i in range(12)]
    files = [file_diff(name, 1500) for name in names]
    diff = "".join(files)
    assert len(diff) > 380_000  # about 400,000 characters over 12 files

    text, trimmed = trim_diff(diff)

    assert trimmed
    assert len(text) <= DIFF_MAX_CHARS
    for name in names:
        assert f"diff --git a/{name} b/{name}\n" in text
        assert f"- {name}\n" in text  # the list of changed files
    shown = [name for name, chunk in zip(names, files, strict=True) if chunk in text]
    assert shown == names[: len(shown)]  # whole files, in diff order
    assert 0 < len(shown) < 12
    note = f"[diff trimmed: {len(shown)} of 12 files shown in full; read the others with the Read"
    assert note in text
    assert re.search(r"Changed files \(12\):", text)


def test_headers_alone_over_the_limit_still_fit() -> None:
    diff = "".join(file_diff(f"f{i}.py", 1) for i in range(50))
    text, trimmed = trim_diff(diff, limit=2_000)
    assert trimmed
    assert len(text) <= 2_000
    assert text.endswith("read the others with the Read tool]\n")

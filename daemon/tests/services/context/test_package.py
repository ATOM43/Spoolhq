"""services/context: the packaged template and the rules around template source."""

import shutil
import subprocess
import zipfile
from importlib import resources
from pathlib import Path

import pytest

from spoolhq.services.context import render as render_module
from tests.conftest import TESTS_DIR

CONTEXT_SRC = TESTS_DIR.parent / "src" / "spoolhq" / "services" / "context"
TEMPLATE_IN_WHEEL = "spoolhq/services/context/prompts/implementer.md.j2"


def test_default_template_is_package_data() -> None:
    template = resources.files("spoolhq.services.context").joinpath("prompts", "implementer.md.j2")
    assert template.is_file()
    assert "<ticket>" in template.read_text(encoding="utf-8")


def test_template_is_loaded_through_importlib_resources() -> None:
    source = (CONTEXT_SRC / "render.py").read_text(encoding="utf-8")
    assert "resources.files(PACKAGE)" in source
    assert "__file__" not in source


def test_untrusted_text_is_never_template_source() -> None:
    for path in sorted(CONTEXT_SRC.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "from_string" not in source, path
        assert "Template(" not in source.replace("PromptTemplate(", ""), path


def test_package_name_matches_the_module() -> None:
    assert render_module.PACKAGE == "spoolhq.services.context"


@pytest.mark.integration
def test_template_is_in_the_built_wheel(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is not on PATH")
    subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [uv, "build", "--wheel", "--out-dir", str(tmp_path), str(TESTS_DIR.parent)],
        capture_output=True,
        text=True,
        check=True,
        timeout=300,
    )
    [wheel] = tmp_path.glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert TEMPLATE_IN_WHEEL in names
    assert TEMPLATE_IN_WHEEL.replace("implementer", "reviewer") in names

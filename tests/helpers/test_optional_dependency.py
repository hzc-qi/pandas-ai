"""Unit tests for the import_optional_dependency function.

Source: Taken from pandas/tests/test_optional_dependency.py
"""

import sys
import types

import pytest

from pandasai.helpers._optional import VERSIONS, import_optional_dependency


def test_import_optional():
    match = "Missing .*notapackage.* pip .* conda .* notapackage"
    with pytest.raises(ImportError, match=match) as exc_info:
        import_optional_dependency("notapackage")
    # The original exception should be there as context:
    assert isinstance(exc_info.value.__context__, ImportError)

    result = import_optional_dependency("notapackage", errors="ignore")
    assert result is None


def test_xlrd_version_fallback():
    pytest.importorskip("xlrd")
    import_optional_dependency("xlrd")


def test_bad_version(monkeypatch):
    name = "fakemodule"
    module = types.ModuleType(name)
    module.__version__ = "0.9.0"
    sys.modules[name] = module
    monkeypatch.setitem(VERSIONS, name, "1.0.0")

    match = "Pandas requires .*1.0.0.* of .fakemodule.*'0.9.0'"
    with pytest.raises(ImportError, match=match):
        import_optional_dependency("fakemodule")

    # Test min_version parameter
    result = import_optional_dependency("fakemodule", min_version="0.8")
    assert result is module

    with pytest.warns(UserWarning):
        result = import_optional_dependency("fakemodule", errors="warn")
    assert result is None

    module.__version__ = "1.0.0"  # exact match is OK
    result = import_optional_dependency("fakemodule")
    assert result is module


def test_submodule(monkeypatch):
    # Create a fake module with a submodule
    name = "fakemodule"
    module = types.ModuleType(name)
    module.__version__ = "0.9.0"
    sys.modules[name] = module
    sub_name = "submodule"
    submodule = types.ModuleType(sub_name)
    setattr(module, sub_name, submodule)
    sys.modules[f"{name}.{sub_name}"] = submodule
    monkeypatch.setitem(VERSIONS, name, "1.0.0")

    match = "Pandas requires .*1.0.0.* of .fakemodule.*'0.9.0'"
    with pytest.raises(ImportError, match=match):
        import_optional_dependency("fakemodule.submodule")

    with pytest.warns(UserWarning):
        result = import_optional_dependency("fakemodule.submodule", errors="warn")
    assert result is None

    module.__version__ = "1.0.0"  # exact match is OK
    result = import_optional_dependency("fakemodule.submodule")
    assert result is submodule


def test_no_version_raises(monkeypatch):
    name = "fakemodule"
    module = types.ModuleType(name)
    sys.modules[name] = module
    monkeypatch.setitem(VERSIONS, name, "1.0.0")

    with pytest.raises(ImportError, match="Can't determine .* fakemodule"):
        import_optional_dependency(name)

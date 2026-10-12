from app.tools.python_analyzer import analyze_python_source, explain_traceback

SAMPLE_TRACEBACK = '''Traceback (most recent call last):
  File "main.py", line 3, in <module>
    print(total)
NameError: name 'total' is not defined'''


def test_valid_code_is_reported_ok():
    code = (
        "import os\n"
        "from math import sqrt\n"
        "\n"
        "def add(a, b):\n"
        "    return a + b\n"
        "\n"
        "class Box:\n"
        "    def size(self):\n"
        "        return 1\n"
    )
    result = analyze_python_source(code)
    assert result["ok"] is True
    assert result["syntax_error"] is None
    assert [f["name"] for f in result["functions"]] == ["add", "size"]
    assert result["functions"][0]["args"] == ["a", "b"]
    assert [c["name"] for c in result["classes"]] == ["Box"]
    assert result["classes"][0]["methods"] == ["size"]
    assert [i["module"] for i in result["imports"]] == ["os", "math"]


def test_syntax_error_reports_line():
    result = analyze_python_source("def broken(:\n    pass\n")
    assert result["ok"] is False
    assert result["syntax_error"]["line"] == 1
    assert result["syntax_error"]["message"]


def test_traceback_is_explained():
    result = explain_traceback(SAMPLE_TRACEBACK)
    assert result["ok"] is True
    assert result["exception_type"] == "NameError"
    assert result["message"] == "name 'total' is not defined"
    assert result["last_frame"] == {"file": "main.py", "line": 3}
    assert "defined" in result["hint"]


def test_text_without_exception_line_is_not_ok():
    result = explain_traceback("just some words")
    assert result["ok"] is False
    assert result["exception_type"] is None
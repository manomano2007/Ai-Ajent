
import ast
import re
from typing import Any

FRAME_PATTERN = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+)')
EXCEPTION_PATTERN = re.compile(r"^(?P<type>[A-Za-z_][\w.]*)(?::\s*(?P<message>.*))?$")

DEFAULT_HINT = "Read the message carefully and check the line shown in the last frame."

EXCEPTION_HINTS = {
    "SyntaxError": "Python could not read this code. Check the line shown for a missing colon, bracket, or quote.",
    "IndentationError": "Indentation is wrong. Python groups code blocks by indentation, so use the same number of spaces for each level (usually 4).",
    "NameError": "A variable or function is used before it is defined, or its name is misspelled.",
    "TypeError": "A function or operator received a value of the wrong type, or the wrong number of arguments.",
    "AttributeError": "The object does not have the attribute or method you used. Use type(obj) to check what the object really is.",
    "KeyError": "A dictionary key does not exist. Use dict.get(key) or check 'key in dict' first.",
    "IndexError": "A list index is outside the list's range. Check the length with len(items).",
    "ZeroDivisionError": "A number was divided by zero. Check the divisor before dividing.",
    "ValueError": "A function received the right type of value, but a value it cannot use.",
    "ModuleNotFoundError": "The module is not installed, or its name is misspelled. Install it with pip or check the import name.",
    "ImportError": "A name could not be imported from the module. Check the spelling and the installed version.",
    "FileNotFoundError": "The file path does not exist. Check the path and the folder the program runs from.",
    "PermissionError": "The program is not allowed to access that file or folder.",
    "RecursionError": "A function calls itself too many times. Check that the recursion has a stop condition.",
}


def _syntax_error_result(line: int | None, column: int | None, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "syntax_error": {"line": line, "column": column, "message": message},
        "functions": [],
        "classes": [],
        "imports": [],
        "note": "This is a verified syntax error from Python's parser. Logic bugs are not checked by this tool.",
    }


def analyze_python_source(source: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source, filename="<submitted code>")
    except SyntaxError as exc:
        return _syntax_error_result(exc.lineno, exc.offset, exc.msg or str(exc))
    except ValueError as exc:
        return _syntax_error_result(None, None, str(exc))

    functions = []
    classes = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                }
            )
        elif isinstance(node, ast.ClassDef):
            methods = [
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes.append({"name": node.name, "line": node.lineno, "methods": methods})
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "line": node.lineno, "kind": "import"})
        elif isinstance(node, ast.ImportFrom):
            module_name = "." * (node.level or 0) + (node.module or "")
            imports.append({"module": module_name, "line": node.lineno, "kind": "from"})

    return {
        "ok": True,
        "syntax_error": None,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "note": "Syntax is valid. Static checks cannot prove that the program has no logic bugs.",
    }


def explain_traceback(text: str) -> dict[str, Any]:
    frames = [
        {"file": match.group("file"), "line": int(match.group("line"))}
        for match in FRAME_PATTERN.finditer(text)
    ]

    exception_line = None
    for raw_line in reversed(text.splitlines()):
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line[0].isspace() or line.startswith("Traceback") or line.startswith("File "):
            continue
        exception_line = line.strip()
        break

    match = EXCEPTION_PATTERN.match(exception_line) if exception_line else None
    if match is None:
        return {
            "ok": False,
            "exception_type": None,
            "message": None,
            "frames": frames,
            "last_frame": frames[-1] if frames else None,
            "hint": None,
            "note": "Could not find an exception line such as 'NameError: ...' in the text you pasted.",
        }

    exception_type = match.group("type")
    short_name = exception_type.split(".")[-1]
    return {
        "ok": True,
        "exception_type": exception_type,
        "message": match.group("message") or "",
        "frames": frames,
        "last_frame": frames[-1] if frames else None,
        "hint": EXCEPTION_HINTS.get(short_name, DEFAULT_HINT),
        "note": "The hint describes this exception type in general. It does not confirm the cause in your code.",
    }

import os
import re
import ast
import subprocess

def patch_python_file(file_path: str, line: int, col: int, replacement: str) -> bool:
    """
    Patches a Python file (.py or .spec.py) using AST node location matching.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        target_node = None

        # Traverse AST and find the closest Call expression on the target line
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if hasattr(node, "lineno") and node.lineno == line:
                    if col is None or (hasattr(node, "col_offset") and node.col_offset <= col):
                        if target_node is None or (node.col_offset > target_node.col_offset):
                            target_node = node

        if target_node:
            lines = source.splitlines()
            start_line = target_node.lineno - 1
            start_col = target_node.col_offset

            # In Python 3.8+, AST nodes have end_lineno and end_col_offset
            if hasattr(target_node, "end_lineno") and target_node.end_lineno is not None:
                end_line = target_node.end_lineno - 1
                end_col = target_node.end_col_offset
            else:
                # Fallback: scan forward on target line to match parentheses
                end_line = start_line
                target_str = lines[start_line][start_col:]
                paren_start = target_str.find("(")
                if paren_start != -1:
                    open_parens = 1
                    idx = paren_start + 1
                    while idx < len(target_str) and open_parens > 0:
                        char = target_str[idx]
                        if char == "(":
                            open_parens += 1
                        elif char == ")":
                            open_parens -= 1
                        idx += 1
                    end_col = start_col + idx
                else:
                    end_col = len(lines[start_line])

            # Reconstruct code with replacement
            if start_line == end_line:
                lines[start_line] = lines[start_line][:start_col] + replacement + lines[start_line][end_col:]
            else:
                # Multi-line node replacement
                lines[start_line] = lines[start_line][:start_col] + replacement
                lines[end_line] = lines[end_line][end_col:]
                # Remove lines in between
                del lines[start_line + 1 : end_line]

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            print(f"[Patcher Python] Successfully patched {file_path} via AST coordinates.")
            return True
            
        return False
    except Exception as err:
        print(f"[Patcher Python] AST parsing/patching failed: {err}")
        return False

def patch_typescript_file_via_babel(file_path: str, line: int, col: int, replacement: str) -> bool:
    """
    Patches a TS/JS file by invoking the Node ts_patcher.js utility.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        js_patcher_path = os.path.join(current_dir, "ts_patcher.js")
        
        # Spawn Node.js subprocess to execute AST patching via Babel
        cmd = ["node", js_patcher_path, file_path, str(line), str(col if col is not None else ""), replacement]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"[Patcher TS] Successfully patched {file_path} via Babel AST.")
            return True
        else:
            print(f"[Patcher TS] Node Babel script failed: {result.stderr.strip()}")
            return False
    except Exception as err:
        print(f"[Patcher TS] Failed to run Node JS patcher: {err}")
        return False

def patch_file_via_text_slice(file_path: str, line: int, col: int, replacement: str) -> bool:
    """
    Fallback coordinate-based text-slice patching.
    Balanced parenthesis scanning to replace the specific locator call.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        if not (1 <= line <= len(lines)):
            return False

        target_line = lines[line - 1]
        
        if col is None or col < 0 or col >= len(target_line):
            # Regex replacement for standard locators on that line
            prefixes = [r"page\.locator\([^)]*\)", r"page\.get_by_[a-z_]+\([^)]*\)", r"page\.getBy[A-Za-z]+\([^)]*\)"]
            for pattern in prefixes:
                match = re.search(pattern, target_line)
                if match:
                    new_line = target_line[:match.start()] + replacement + target_line[match.end():]
                    lines[line - 1] = new_line
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines) + "\n")
                    return True
            return False

        # Scan backward from column to find standard Playwright call prefix 'page.'
        start_idx = col
        while start_idx > 0 and not target_line[start_idx:].startswith("page."):
            start_idx -= 1
        
        if not target_line[start_idx:].startswith("page."):
            start_idx = col

        # Search for first opening parenthesis after prefix
        paren_start = target_line.find("(", start_idx)
        if paren_start == -1:
            return False
            
        # Match closing parenthesis
        open_parens = 1
        idx = paren_start + 1
        while idx < len(target_line) and open_parens > 0:
            char = target_line[idx]
            if char == "(":
                open_parens += 1
            elif char == ")":
                open_parens -= 1
            idx += 1
            
        if open_parens == 0:
            end_idx = idx
            new_line = target_line[:start_idx] + replacement + target_line[end_idx:]
            lines[line - 1] = new_line
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            print(f"[Patcher Fallback] Successfully patched {file_path} via text-slice scan.")
            return True
            
        return False
    except Exception as err:
        print(f"[Patcher Fallback] Text-slice patching failed: {err}")
        return False

def patch_source_file(file_path: str, line: int, col: int, replacement: str) -> bool:
    """
    Unified entrypoint to hot-patch failing Playwright locators inside source files.
    Determines file type and attempts appropriate AST-based patching, falling back
    gracefully to coordinate-based text slicing.
    """
    if not file_path or not os.path.exists(file_path):
        print(f"[Patcher] Target file path '{file_path}' does not exist or is invalid.")
        return False
        
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".py":
        # Try Python AST patching
        if patch_python_file(file_path, line, col, replacement):
            return True
    elif ext in (".ts", ".js", ".tsx", ".jsx"):
        # Try TS/JS Babel AST patching
        if patch_typescript_file_via_babel(file_path, line, col, replacement):
            return True

    # Fallback to bulletproof text slice scanning if AST fails
    return patch_file_via_text_slice(file_path, line, col, replacement)

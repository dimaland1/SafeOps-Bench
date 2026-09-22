"""Robust Bash AST parsing and CLI flag decomposition engine using Tree-sitter."""

import re
import shlex
from typing import List, Optional, Set, Tuple

# Try loading tree-sitter-bash if compiled bindings are available
_HAS_TREE_SITTER = False
try:
    from tree_sitter import Language, Parser
    import tree_sitter_bash as tsbash
    _BASH_LANGUAGE = Language(tsbash.language())
    _PARSER = Parser(_BASH_LANGUAGE)
    _HAS_TREE_SITTER = True
except Exception:
    _HAS_TREE_SITTER = False


def extract_commands_from_script(script_content: str) -> List[Tuple[str, List[str]]]:
    """Extracts all commands and their argument lists from a bash script or one-liner.
    Uses tree-sitter-bash when available, with a resilient fallback.
    """
    if not script_content or not script_content.strip():
        return []

    # Strip markdown code fences if present
    cleaned = script_content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    if _HAS_TREE_SITTER:
        return _extract_via_tree_sitter(cleaned)
    else:
        return _extract_via_fallback(cleaned)


def _split_subcommands(cmd_name: str, args: List[str]) -> List[Tuple[str, List[str]]]:
    """Helper to detect and split embedded subcommands such as find -exec <cmd> <args>..."""
    extracted = []
    if cmd_name == "sudo" and args:
        cmd_name = args[0]
        args = args[1:]

    if cmd_name == "find":
        for exec_flag in ("-exec", "-execdir"):
            if exec_flag in args:
                idx = args.index(exec_flag)
                find_args = args[:idx + 1]
                sub_tokens = args[idx + 1:]
                sub_clean = [t for t in sub_tokens if t not in (";", "\\;", "+", "{}")]
                if sub_clean:
                    sub_cmd = sub_clean[0]
                    sub_args = sub_clean[1:]
                    extracted.extend(_split_subcommands(sub_cmd, sub_args))
                args = find_args
                break

    extracted.append((cmd_name, args))
    return extracted


def _extract_via_tree_sitter(script_content: str) -> List[Tuple[str, List[str]]]:
    """Parse tree using tree-sitter-bash."""
    tree = _PARSER.parse(bytes(script_content, "utf8"))
    commands: List[Tuple[str, List[str]]] = []

    def traverse(node):
        if node.type == "command":
            cmd_name = None
            args: List[str] = []
            for child in node.children:
                if child.type == "command_name":
                    cmd_name = script_content[child.start_byte:child.end_byte]
                elif child.type in ("word", "string", "raw_string"):
                    token = script_content[child.start_byte:child.end_byte]
                    # Strip leading/trailing quotes if wrapped
                    if (token.startswith('"') and token.endswith('"')) or \
                       (token.startswith("'") and token.endswith("'")):
                        token = token[1:-1]
                    args.append(token)
            if cmd_name:
                commands.extend(_split_subcommands(cmd_name, args))

        for child in node.children:
            traverse(child)

    traverse(tree.root_node)
    return commands


def _extract_via_fallback(script_content: str) -> List[Tuple[str, List[str]]]:
    """Resilient fallback parser for platforms without compiled tree-sitter bindings."""
    commands: List[Tuple[str, List[str]]] = []
    # Split pipeline, semicolons, and logic operators
    raw_statements = re.split(r"[;&|]+|\n", script_content)
    for stmt in raw_statements:
        clean_stmt = stmt.strip()
        if not clean_stmt or clean_stmt.startswith("#"):
            continue
        try:
            tokens = shlex.split(clean_stmt)
        except ValueError:
            tokens = clean_stmt.split()

        if not tokens:
            continue

        cmd = tokens[0]
        args = tokens[1:]
        commands.extend(_split_subcommands(cmd, args))

    return commands


def normalize_flags(args: List[str], command: Optional[str] = None) -> Set[str]:
    """Decomposes compound short flags and normalizes long flags.
    Examples:
      ['-h'] -> {'-h'}
      ['-xvzf'] -> {'-x', '-v', '-z', '-f'}
      ['--max-depth=1'] -> {'--max-depth'}
      ['+L1'] -> {'+L1'}
      ['-type'] (for find) -> {'-type'}
    """
    flags: Set[str] = set()
    find_word_flags = {
        "-type", "-name", "-iname", "-size", "-mtime", "-atime", "-ctime",
        "-maxdepth", "-mindepth", "-exec", "-execdir", "-delete", "-print",
        "-empty", "-perm", "-user", "-group", "-path", "-regex", "-prune"
    }

    for arg in args:
        if arg.startswith("--"):
            # Strip parameter value: '--max-depth=1' -> '--max-depth'
            flag_name = arg.split("=")[0]
            flags.add(flag_name)
        elif arg.startswith("+") and len(arg) > 1:
            # Special flags like lsof '+L1' or '+D'
            flags.add(arg)
        elif arg.startswith("-") and len(arg) > 1:
            if re.match(r"^-[0-9]+$", arg):
                flags.add(arg)
            elif command == "find" or arg in find_word_flags:
                flags.add(arg)
            else:
                for char in arg[1:]:
                    if char.isalnum():
                        flags.add(f"-{char}")
    return flags

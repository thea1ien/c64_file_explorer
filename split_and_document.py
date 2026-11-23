import ast
import os
import re

SOURCE_FILE = "c64_file_explorer.py"
SRC_DIR = "src"
REF_FILE = "ARCHITECTURE_REFERENCE.md"

def detect_ui_mode(node):
	"""Tags a node as Pygame-only, Terminal-only, Hybrid, or Core."""
	code_dump = ast.dump(node).lower()
	has_pygame = "pygame" in code_dump
	has_std = any(k in code_dump for k in ["curses", "msvcrt", "termios", "print(", "input("])
	
	if has_pygame and not has_std:
		return "[PYGAME ONLY]"
	elif has_std and not has_pygame:
		return "[STANDARD/TERM ONLY]"
	elif has_pygame and has_std:
		return "[HYBRID: PYGAME + STD]"
	return "[CORE / MODE-AGNOSTIC]"

def get_summary(node):
	doc = ast.get_docstring(node)
	if doc:
		lines = doc.strip().splitlines()
		return lines[0].strip() if lines else "No description."
	if isinstance(node, ast.FunctionDef):
		args = [a.arg for a in node.args.args if a.arg != "self"]
		return f"Params: ({', '.join(args)})" if args else "No external parameters."
	return "System class definition."

def route_to_tree_path(node):
	"""Routes every top-level AST node into a C/C++-style subfolder & dedicated file."""
	if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)):
		return os.path.join("01_core", "01_imports_and_constants.py")

	if isinstance(node, ast.ClassDef):
		n = node.name.lower()
		# Core VFS & Base classes must load before subclasses
		if "registry" in n:
			return os.path.join("01_core", "03_vfs_registry.py")
		if "basecmd" in n or "cmdbase" in n:
			return os.path.join("03_drivers_cmd", "01_cmd_base.py")
		if "base" in n or "vfs" in n:
			return os.path.join("01_core", "02_vfs_base.py")

		# Individual Commodore Disk Handlers (1 class = 1 file)
		if "d64" in n:
			return os.path.join("02_drivers_commodore", "01_d64.py")
		if "g64" in n:
			return os.path.join("02_drivers_commodore", "02_g64.py")
		if "d71" in n:
			return os.path.join("02_drivers_commodore", "03_d71.py")
		if "d81" in n:
			return os.path.join("02_drivers_commodore", "04_d81.py")
		if any(k in n for k in ["t64", "tap", "prg", "p00", "lnx", "arc"]):
			clean_name = re.sub(r'(filesystem|plugin|handler)', '', n).strip('_') or "archives"
			return os.path.join("02_drivers_commodore", f"05_{clean_name}.py")

		# Individual CMD Device Handlers (1 class = 1 file)
		if "dhd" in n:
			return os.path.join("03_drivers_cmd", "02_dhd.py")
		if "d2m" in n:
			return os.path.join("03_drivers_cmd", "03_d2m.py")
		if "d4m" in n:
			return os.path.join("03_drivers_cmd", "04_d4m.py")
		if "dnp" in n:
			return os.path.join("03_drivers_cmd", "05_dnp.py")

		# Any remaining UI or helper classes
		return os.path.join("01_core", f"04_{n}.py")

	if isinstance(node, ast.FunctionDef):
		n = node.name.lower()
		mode = detect_ui_mode(node)

		if any(k in n for k in ["petscii", "ascii", "cbm_", "convert", "format_size"]):
			return os.path.join("01_core", "05_petscii_and_utils.py")
		if "sector" in n or "hex" in n:
			return os.path.join("04_sector_editor", f"{n}.py")
		if "PYGAME ONLY" in mode or "pygame" in n:
			return os.path.join("05_ui_pygame", f"{n}.py")
		if "STANDARD/TERM" in mode or any(k in n for k in ["term", "curses", "console"]):
			return os.path.join("06_ui_terminal", f"{n}.py")
		if any(k in n for k in ["copy", "delete", "rename", "activate", "mount", "navigate"]):
			return os.path.join("07_app_runtime", f"{n}.py")
		return os.path.join("07_app_runtime", "00_shared_helpers.py")

	# Main execution block (if __name__ == "__main__":)
	return os.path.join("07_app_runtime", "99_main_entry.py")

def split_tree_and_document():
	if not os.path.exists(SOURCE_FILE):
		print(f"❌ Could not find '{SOURCE_FILE}'.")
		return

	with open(SOURCE_FILE, "r", encoding="utf-8") as f:
		source_code = f.read()
		source_lines = source_code.splitlines(keepends=True)

	tree = ast.parse(source_code, filename=SOURCE_FILE)
	tree_files = {}
	tree_docs = {}
	driver_matrix = {}

	for node in tree.body:
		rel_path = route_to_tree_path(node).replace("\\", "/")
		tree_files.setdefault(rel_path, [])
		tree_docs.setdefault(rel_path, {"vars": [], "funcs": [], "classes": []})

		start_line = node.decorator_list.lineno - 1 if getattr(node, "decorator_list", None) else node.lineno - 1
		chunk = "".join(source_lines[start_line:node.end_lineno]) + "\n\n"
		tree_files[rel_path].append(chunk)

		if isinstance(node, ast.Assign):
			for target in node.targets:
				if isinstance(target, ast.Name):
					val_preview = ast.unparse(node.value)[:60].replace("\n", " ")
					tree_docs[rel_path]["vars"].append(f"- **`{target.id}`**: `{val_preview}`")

		elif isinstance(node, ast.FunctionDef):
			mode_tag = detect_ui_mode(node)
			tree_docs[rel_path]["funcs"].append(f"- **`{node.name}()`** {mode_tag} — {get_summary(node)}")

		elif isinstance(node, ast.ClassDef):
			bases = [ast.unparse(b) for b in node.bases]
			base_str = f" *(Inherits: `{', '.join(bases)}`)*" if bases else ""
			class_lines = [f"#### Class: `{node.name}`{base_str}"]

			is_driver = any(k in rel_path for k in ["drivers_", "vfs_base"])
			if is_driver:
				driver_matrix[node.name] = set()

			for item in node.body:
				if isinstance(item, ast.FunctionDef):
					mode_tag = detect_ui_mode(item)
					scope = f"*(Bound to `{node.name}` instance)*"
					class_lines.append(f"  - **`{item.name}()`** {mode_tag} {scope}: {get_summary(item)}")
					if is_driver:
						driver_matrix[node.name].add(item.name)

			tree_docs[rel_path]["classes"].append("\n".join(class_lines))

	# Write out the directory tree
	for rel_path, chunks in sorted(tree_files.items()):
		full_path = os.path.join(SRC_DIR, rel_path)
		os.makedirs(os.path.dirname(full_path), exist_ok=True)
		with open(full_path, "w", encoding="utf-8") as out_f:
			out_f.writelines(chunks)
		print(f"📂 Wrote: {full_path}")

	# Write ARCHITECTURE_REFERENCE.md
	with open(REF_FILE, "w", encoding="utf-8") as ref:
		ref.write("# 🌳 C64 File Explorer — Modular Tree & Routine Reference\n\n")
		if driver_matrix:
			ref.write("## 🔌 Disk & CMD Handler Parity Matrix\n\n")
			drivers = sorted(driver_matrix.keys())
			methods = sorted({m for s in driver_matrix.values() for m in s if not m.startswith("__")})
			ref.write("| Internal Method | " + " | ".join(drivers) + " |\n")
			ref.write("| --- | " + " | ".join(["---"] * len(drivers)) + " |\n")
			for m in methods:
				row = [f"✅ `{m}`" if m in driver_matrix[d] else "❌ *(None)*" for d in drivers]
				ref.write(f"| **`{m}()`** | " + " | ".join(row) + " |\n")
			ref.write("\n---\n\n")

		for rel_path in sorted(tree_docs.keys()):
			data = tree_docs[rel_path]
			ref.write(f"## 📄 `src/{rel_path}`\n\n")
			if data["vars"]:
				ref.write("### 🏷️ Variables & Constants\n" + "\n".join(data["vars"]) + "\n\n")
			if data["funcs"]:
				ref.write("### ⚙️ Standalone Routines\n" + "\n".join(data["funcs"]) + "\n\n")
			if data["classes"]:
				ref.write("### 🧩 Classes & Instance-Bound Routines\n" + "\n\n".join(data["classes"]) + "\n\n")
			ref.write("---\n\n")

	print(f"📘 Updated reference guide: {REF_FILE}")

if __name__ == "__main__":
	split_tree_and_document()

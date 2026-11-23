import os
import py_compile
import shutil

SRC_DIR = "src"
OUTPUT_FILE = "c64_file_explorer.py"
BACKUP_FILE = "c64_file_explorer.py.bak"

# Explicit folder priority ensures base classes and constants load before drivers and UI
FOLDER_ORDER = [
	"01_core",
	"02_drivers_commodore",
	"03_drivers_cmd",
	"04_sector_editor",
	"05_ui_pygame",
	"06_ui_terminal",
	"07_app_runtime"
]

def get_ordered_files():
	ordered_files = []
	seen_paths = set()

	# 1. Walk prioritized folders first
	for folder in FOLDER_ORDER:
		folder_path = os.path.join(SRC_DIR, folder)
		if os.path.isdir(folder_path):
			for root, dirs, files in os.walk(folder_path):
				dirs.sort()
				for file in sorted(files):
					if file.endswith(".py"):
						full_path = os.path.join(root, file)
						ordered_files.append(full_path)
						seen_paths.add(os.path.abspath(full_path))

	# 2. Catch any custom subfolders added later
	for root, dirs, files in os.walk(SRC_DIR):
		dirs.sort()
		for file in sorted(files):
			if file.endswith(".py"):
				full_path = os.path.join(root, file)
				if os.path.abspath(full_path) not in seen_paths:
					ordered_files.append(full_path)
					seen_paths.add(os.path.abspath(full_path))

	return ordered_files

def build_single_program():
	if not os.path.isdir(SRC_DIR):
		print(f"❌ Error: '{SRC_DIR}/' folder not found. Run split_and_document.py first.")
		return

	# Automatically create a safety backup of your existing working program
	if os.path.exists(OUTPUT_FILE) and not os.path.exists(BACKUP_FILE):
		shutil.copy2(OUTPUT_FILE, BACKUP_FILE)
		print(f"🛡️  Created safety backup: '{BACKUP_FILE}'")

	module_files = get_ordered_files()
	if not module_files:
		print(f"❌ Error: No .py files found inside '{SRC_DIR}/'.")
		return

	compiled_lines = [
		"# ============================================================================\n",
		"# C64 FILE EXPLORER - AUTO-GENERATED SINGLE-FILE BUILD\n",
		"# ============================================================================\n\n"
	]

	seen_imports = set()
	main_entry_blocks = []

	for filepath in module_files:
		rel_path = os.path.relpath(filepath, SRC_DIR).replace("\\", "/")
		header = f"\n# {'-' * 76}\n# MODULE: src/{rel_path}\n# {'-' * 76}\n\n"

		with open(filepath, "r", encoding="utf-8") as f:
			lines = f.readlines()

		# Always defer 99_main_entry.py to the absolute bottom of the stitched file
		if os.path.basename(filepath) == "99_main_entry.py":
			main_entry_blocks.append(header)
			main_entry_blocks.extend(lines)
			continue

		compiled_lines.append(header)
		for line in lines:
			stripped = line.strip()
			if (stripped.startswith("import ") or stripped.startswith("from ")) and not line.startswith((" ", "\t")):
				if stripped in seen_imports:
					continue
				seen_imports.add(stripped)
			compiled_lines.append(line)

	# Append the main entry block last so every class and function is defined first
	compiled_lines.extend(main_entry_blocks)

	with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
		out.writelines(compiled_lines)

	# Verify Python bytecode compilation immediately
	try:
		py_compile.compile(OUTPUT_FILE, doraise=True)
		print(f"✅ Stitched {len(module_files)} tree files into '{OUTPUT_FILE}'!")
		print("✅ Bytecode syntax verification passed with zero errors.")
	except py_compile.PyCompileError as e:
		print(f"⚠️  Build generated '{OUTPUT_FILE}', but syntax check reported an issue:\n{e}")

if __name__ == "__main__":
	build_single_program()

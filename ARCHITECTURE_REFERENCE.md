# 🌳 C64 File Explorer — Modular Tree & Routine Reference

## 🔌 Disk & CMD Handler Parity Matrix

| Internal Method | BaseCMDFloppyPlugin | BaseContainerHandler | BaseVFSHandler | D2MFileSystemPlugin | D4MFileSystemPlugin | D64FileSystemHandler | D64FileSystemPlugin | D71FileSystemPlugin | D81FileSystemPlugin | DHDFileSystemPlugin | DNPFileSystemPlugin | DNPNativeHandler | G64FileSystemPlugin | LNXFileSystemPlugin | SharedVFSController | VFSBlockStream |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **`allocate_free_sector()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `allocate_free_sector` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`allocate_virtual_sector_in_bam()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `allocate_virtual_sector_in_bam` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`check_sector_free_status()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `check_sector_free_status` | ✅ `check_sector_free_status` | ✅ `check_sector_free_status` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`check_target_for_duplicate_filename()`** | ❌ *(None)* | ❌ *(None)* | ✅ `check_target_for_duplicate_filename` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`create_1581_partition_sectors()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `create_1581_partition_sectors` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`deallocate_virtual_sector_in_bam()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `deallocate_virtual_sector_in_bam` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`decode_gcr_bits_to_bytes()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `decode_gcr_bits_to_bytes` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`demodulate_track_gcr_to_cache()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `demodulate_track_gcr_to_cache` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`encode_bytes_to_gcr_bits()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `encode_bytes_to_gcr_bits` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`execute_file_activation()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `execute_file_activation` | ❌ *(None)* |
| **`extract_file_bytes()`** | ❌ *(None)* | ❌ *(None)* | ✅ `extract_file_bytes` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `extract_file_bytes` | ✅ `extract_file_bytes` | ✅ `extract_file_bytes` | ❌ *(None)* | ✅ `extract_file_bytes` | ❌ *(None)* | ✅ `extract_file_bytes` | ✅ `extract_file_bytes` | ❌ *(None)* | ❌ *(None)* |
| **`find_next_free_allocation_block()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `find_next_free_allocation_block` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`flush_dhd_to_disk()`** | ✅ `flush_dhd_to_disk` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `flush_dhd_to_disk` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`get_bam_state()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_bam_state` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`get_cached_sector_bit_offset()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_cached_sector_bit_offset` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`get_d71_linear_sector_index()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_d71_linear_sector_index` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`get_d71_linear_sector_offset()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_d71_linear_sector_offset` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`get_d81_linear_sector_index()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_d81_linear_sector_index` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`get_dnp_bam_matrix()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_dnp_bam_matrix` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`get_partition_creation_track_matrix()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_partition_creation_track_matrix` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`get_raw_block()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_raw_block` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_raw_block` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`get_raw_gcr_track_stream()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_raw_gcr_track_stream` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`get_total_blocks()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `get_total_blocks` |
| **`list_directory()`** | ❌ *(None)* | ❌ *(None)* | ✅ `list_directory` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `list_directory` | ✅ `list_directory` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `list_directory` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`list_directory_entries()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `list_directory_entries` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`mount()`** | ✅ `mount` | ✅ `mount` | ✅ `mount` | ❌ *(None)* | ❌ *(None)* | ✅ `mount` | ✅ `mount` | ✅ `mount` | ✅ `mount` | ✅ `mount` | ✅ `mount` | ✅ `mount` | ✅ `mount` | ✅ `mount` | ❌ *(None)* | ❌ *(None)* |
| **`navigate_backward()`** | ❌ *(None)* | ❌ *(None)* | ✅ `navigate_backward` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `navigate_backward` | ✅ `navigate_backward` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`navigate_forward()`** | ✅ `navigate_forward` | ❌ *(None)* | ✅ `navigate_forward` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `navigate_forward` | ✅ `navigate_forward` | ✅ `navigate_forward` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`print_current_directory()`** | ❌ *(None)* | ✅ `print_current_directory` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`read_block()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `read_block` |
| **`read_virtual_sector()`** | ✅ `read_virtual_sector` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `read_virtual_sector` | ✅ `read_virtual_sector` | ✅ `read_virtual_sector` | ✅ `read_virtual_sector` | ✅ `read_virtual_sector` | ✅ `read_virtual_sector` | ✅ `read_virtual_sector` | ✅ `read_virtual_sector` | ✅ `read_virtual_sector` | ❌ *(None)* | ❌ *(None)* |
| **`toggle_sector_allocation_status()`** | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `toggle_sector_allocation_status` | ✅ `toggle_sector_allocation_status` | ❌ *(None)* | ✅ `toggle_sector_allocation_status` | ✅ `toggle_sector_allocation_status` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |
| **`write_virtual_sector()`** | ✅ `write_virtual_sector` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* | ✅ `write_virtual_sector` | ✅ `write_virtual_sector` | ✅ `write_virtual_sector` | ❌ *(None)* | ✅ `write_virtual_sector` | ✅ `write_virtual_sector` | ✅ `write_virtual_sector` | ❌ *(None)* | ❌ *(None)* | ❌ *(None)* |

---

## 📄 `src/01_core/01_imports_and_constants.py`

### 🏷️ Variables & Constants
- **`MANDATORY_LIBS`**: `{'curses': 'windows-curses' if sys.platform.startswith('win'`
- **`FONT_STREAM_ROM`**: `['AAEAAAALAIAAAwAwT1MvMljSrI0AAAE4AAAAYGNtYXCRDujwAAAEFAAACH`

---

## 📄 `src/01_core/02_vfs_base.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `SharedVFSController`
  - **`execute_file_activation()`** [CORE / MODE-AGNOSTIC] *(Bound to `SharedVFSController` instance)*: Unified router handling Enter/Return operations across all interface modes.

#### Class: `BaseVFSHandler`
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseVFSHandler` instance)*: Params: (raw_payload, archive_name)
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseVFSHandler` instance)*: No external parameters.
  - **`list_directory()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseVFSHandler` instance)*: No external parameters.
  - **`check_target_for_duplicate_filename()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseVFSHandler` instance)*: Scans the active directory blocks for a matching filename.
  - **`extract_file_bytes()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseVFSHandler` instance)*: Params: (vfs_meta_node)
  - **`navigate_forward()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseVFSHandler` instance)*: Params: (track, sector, name)
  - **`navigate_backward()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseVFSHandler` instance)*: No external parameters.

#### Class: `VFSBlockStream`
  - **`read_block()`** [CORE / MODE-AGNOSTIC] *(Bound to `VFSBlockStream` instance)*: Params: (block_index)
  - **`get_total_blocks()`** [CORE / MODE-AGNOSTIC] *(Bound to `VFSBlockStream` instance)*: No external parameters.

#### Class: `BaseContainerHandler`
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseContainerHandler` instance)*: Params: (vfs_stream)
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseContainerHandler` instance)*: No external parameters.
  - **`print_current_directory()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseContainerHandler` instance)*: No external parameters.

---

## 📄 `src/01_core/03_vfs_registry.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `VFSDriverRegistry`
  - **`register_format()`** [CORE / MODE-AGNOSTIC] *(Bound to `VFSDriverRegistry` instance)*: Params: (cls, extension, handler_class)
  - **`is_supported()`** [CORE / MODE-AGNOSTIC] *(Bound to `VFSDriverRegistry` instance)*: Params: (cls, filename)
  - **`instantiate_handler()`** [CORE / MODE-AGNOSTIC] *(Bound to `VFSDriverRegistry` instance)*: Params: (cls, filename, payload_bytes)

#### Class: `ImageGeometryRegistry`
  - **`get_sectors_in_track()`** [CORE / MODE-AGNOSTIC] *(Bound to `ImageGeometryRegistry` instance)*: Params: (profile_name, track, total_payload_blocks)
  - **`translate_ts_to_block_index()`** [CORE / MODE-AGNOSTIC] *(Bound to `ImageGeometryRegistry` instance)*: Params: (profile_name, track, sector, total_payload_blocks)

---

## 📄 `src/01_core/04_bameditorscreen.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `BAMEditorScreen`
  - **`get_disk_geometry()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMEditorScreen` instance)*: Fact-aligned hardware layout analyzer returning total tracks
  - **`calculate_live_free_blocks()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMEditorScreen` instance)*: Scans the live driver array bitmasks in real-time to compute the exact free blocks.
  - **`run_editor()`** [STANDARD/TERM ONLY] *(Bound to `BAMEditorScreen` instance)*: Main independent orchestration loop rendering the standalone BAM layout screen.

---

## 📄 `src/01_core/04_bammanager.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `BAMManager`
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMManager` instance)*: Params: (driver_instance, bam_track)
  - **`_generate_bam_parameters()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMManager` instance)*: Fact-aligned hardware layout profiles mapping exact byte limits
  - **`load_bam_from_disk()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMManager` instance)*: Commands driver to read raw BAM sectors and decodes their allocation masks.
  - **`flush_bam_changes_to_media()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMManager` instance)*: Compiles the in-memory working bit grid maps back into accurate hardware hex
  - **`check_sector_status()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMManager` instance)*: Returns the live buffered state of a sector cell: True = Free, False = Used.
  - **`toggle_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMManager` instance)*: Flips the buffer allocation state of a specific coordinate cell natively.
  - **`allocate_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMManager` instance)*: Explicitly marks a block as used (False). Vital for future file save engines!
  - **`free_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMManager` instance)*: Explicitly marks a block as free (True). Vital for future delete routines!
  - **`count_free_blocks()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMManager` instance)*: Natively scans the bit grid tables to calculate live or historical sector totals.
  - **`flush_bam_changes_to_media()`** [CORE / MODE-AGNOSTIC] *(Bound to `BAMManager` instance)*: Compiles the in-memory working bit grid maps back into accurate hardware hex

---

## 📄 `src/01_core/04_configurationmanager.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `ConfigurationManager`
  - **`load_application_settings()`** [CORE / MODE-AGNOSTIC] *(Bound to `ConfigurationManager` instance)*: No external parameters.
  - **`save_application_settings()`** [CORE / MODE-AGNOSTIC] *(Bound to `ConfigurationManager` instance)*: Params: (config_dict)
  - **`is_version_newer()`** [CORE / MODE-AGNOSTIC] *(Bound to `ConfigurationManager` instance)*: Params: (version_v1, version_v2)
  - **`trigger_program_reboot()`** [CORE / MODE-AGNOSTIC] *(Bound to `ConfigurationManager` instance)*: No external parameters.

---

## 📄 `src/01_core/04_hostfileblockstream.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `HostFileBlockStream` *(Inherits: `VFSBlockStream`)*
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `HostFileBlockStream` instance)*: Params: (filepath)
  - **`read_block()`** [CORE / MODE-AGNOSTIC] *(Bound to `HostFileBlockStream` instance)*: Params: (block_index)
  - **`get_total_blocks()`** [CORE / MODE-AGNOSTIC] *(Bound to `HostFileBlockStream` instance)*: No external parameters.

---

## 📄 `src/01_core/04_hostsystemscanner.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `HostSystemScanner`
  - **`get_formatted_size()`** [CORE / MODE-AGNOSTIC] *(Bound to `HostSystemScanner` instance)*: Params: (byte_count, is_dir)
  - **`scan_directory()`** [CORE / MODE-AGNOSTIC] *(Bound to `HostSystemScanner` instance)*: Params: (target_path)

---

## 📄 `src/01_core/04_petsciidecoder.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `PETSCIIDecoder`
  - **`decode_name()`** [CORE / MODE-AGNOSTIC] *(Bound to `PETSCIIDecoder` instance)*: Fact-aligned global character translation mapping PETSCII blocks to safe string layouts.

---

## 📄 `src/01_core/04_preloadedbufferblockstream.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `PreloadedBufferBlockStream` *(Inherits: `VFSBlockStream`)*
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `PreloadedBufferBlockStream` instance)*: Params: (raw_byte_buffer)
  - **`read_block()`** [CORE / MODE-AGNOSTIC] *(Bound to `PreloadedBufferBlockStream` instance)*: Params: (block_index)
  - **`get_total_blocks()`** [CORE / MODE-AGNOSTIC] *(Bound to `PreloadedBufferBlockStream` instance)*: No external parameters.

---

## 📄 `src/01_core/04_pygamevisualengine.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `PygameVisualEngine`
  - **`ascii_to_c64_screencode()`** [CORE / MODE-AGNOSTIC] *(Bound to `PygameVisualEngine` instance)*: Params: (text_str)
  - **`launch_graphical_mirror()`** [PYGAME ONLY] *(Bound to `PygameVisualEngine` instance)*: Spawns an interactive mirror environment displaying dual panels natively inside Pygame.

---

## 📄 `src/01_core/04_tuibameditorrenderer.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `TUIBAMEditorRenderer`
  - **`paint_bam_editor_workspace()`** [STANDARD/TERM ONLY] *(Bound to `TUIBAMEditorRenderer` instance)*: Params: (stdscr, ctx)

---

## 📄 `src/01_core/04_tuicontroller.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `TUIController`
  - **`get_host_free_space_string()`** [CORE / MODE-AGNOSTIC] *(Bound to `TUIController` instance)*: Params: (target_path)
  - **`extract_vfs_file_bytes()`** [CORE / MODE-AGNOSTIC] *(Bound to `TUIController` instance)*: Params: (handler_instance, track, sector)
  - **`establish_bulk_copy_strategy()`** [STANDARD/TERM ONLY] *(Bound to `TUIController` instance)*: Acts precisely like a classic BASIC GOSUB block.
  - **`mine_dnp_entries()`** [CORE / MODE-AGNOSTIC] *(Bound to `TUIController` instance)*: Params: (dnp_handler, track, sector)
  - **`process_scrolling_movement()`** [CORE / MODE-AGNOSTIC] *(Bound to `TUIController` instance)*: Fact-aligned view scrolling manager that ensures selection cursors
  - **`check_target_for_duplicate_filename()`** [CORE / MODE-AGNOSTIC] *(Bound to `TUIController` instance)*: Automated name collision gatekeeper scanning target directories and virtual container

---

## 📄 `src/01_core/04_tuidropdownmenu.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `TUIDropDownMenu`
  - **`draw_menu_card()`** [STANDARD/TERM ONLY] *(Bound to `TUIDropDownMenu` instance)*: Params: (stdscr, menu_idx, active_item_idx, panel_state, global_tui_state)
  - **`show_settings_popup()`** [STANDARD/TERM ONLY] *(Bound to `TUIDropDownMenu` instance)*: Params: (stdscr, global_tui_state)
  - **`show_credits_popup()`** [STANDARD/TERM ONLY] *(Bound to `TUIDropDownMenu` instance)*: Params: (stdscr)

---

## 📄 `src/01_core/04_tuigcrviewerrenderer.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `TUIGCRViewerRenderer`
  - **`paint_gcr_viewer_workspace()`** [STANDARD/TERM ONLY] *(Bound to `TUIGCRViewerRenderer` instance)*: Params: (stdscr, ctx)

---

## 📄 `src/01_core/04_tuirenderer.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `TUIRenderer`
  - **`initialize_colors()`** [STANDARD/TERM ONLY] *(Bound to `TUIRenderer` instance)*: Registers classic Midnight Commander style color palettes into terminal memory.
  - **`draw_top_menubar()`** [STANDARD/TERM ONLY] *(Bound to `TUIRenderer` instance)*: Paints the permanent drop-down menu anchor words across row 0.
  - **`draw_single_panel()`** [STANDARD/TERM ONLY] *(Bound to `TUIRenderer` instance)*: Draws one structural sidebar panel box container window framework.
  - **`draw_footer_hotkeys()`** [STANDARD/TERM ONLY] *(Bound to `TUIRenderer` instance)*: Paints system command function buttons across the last screen row.
  - **`paint_complete_screen()`** [STANDARD/TERM ONLY] *(Bound to `TUIRenderer` instance)*: Redraws the complete twin explorer screen grid canvas cleanly.

---

## 📄 `src/01_core/04_tuisectoreditorrenderer.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `TUISectorEditorRenderer`
  - **`paint_editor_workspace()`** [STANDARD/TERM ONLY] *(Bound to `TUISectorEditorRenderer` instance)*: Params: (stdscr, editor_state)

---

## 📄 `src/02_drivers_commodore/01_d64.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `D64FileSystemPlugin` *(Inherits: `BaseVFSHandler`)*
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemPlugin` instance)*: No external parameters.
  - **`check_sector_free_status()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemPlugin` instance)*: Natively checks the raw 1541 allocation bitmask inside Track 18, Sector 0
  - **`toggle_sector_allocation_status()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemPlugin` instance)*: Natively flips the allocation bit mask for a standard 1541 .d64 image
  - **`extract_file_bytes()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemPlugin` instance)*: Params: (vfs_meta_node)
  - **`read_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemPlugin` instance)*: Passes the sector read request straight down to the 1541 DOS engine.
  - **`write_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemPlugin` instance)*: Production-grade sector modifier with integrated Data Change Guard.

#### Class: `D64FileSystemHandler` *(Inherits: `BaseContainerHandler`)*
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemHandler` instance)*: Params: (vfs_stream, archive_name)
  - **`read_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemHandler` instance)*: Params: (track, sector)
  - **`get_raw_block()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemHandler` instance)*: Params: (track, sector)
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemHandler` instance)*: No external parameters.
  - **`get_bam_state()`** [CORE / MODE-AGNOSTIC] *(Bound to `D64FileSystemHandler` instance)*: Pure Data Engine: Computes the 1541 disk environment from the BAM bitmasks.

---

## 📄 `src/02_drivers_commodore/02_g64.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `G64FileSystemPlugin`
  - **`encode_bytes_to_gcr_bits()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: Computes the 1541 data sector XOR checksum, frames the 260-byte block,
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: Params: (file_bytes, archive_name)
  - **`get_cached_sector_bit_offset()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: Queries the geometry cache map for a sector's bit coordinate position.
  - **`get_raw_gcr_track_stream()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: Natively parses .g64 tables to extract file offsets, track byte sizes,
  - **`read_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: High-level sector fetch hook. Automatically demodulates the requested
  - **`write_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: Production-grade surgical .g64 sector modifier with integrated
  - **`decode_gcr_bits_to_bytes()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: Groups a sequence of bit integers into 5-bit GCR chunks and decodes them.
  - **`demodulate_track_gcr_to_cache()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: 🚨 HARDWARE-REPLICATING LOOK-AHEAD GCR DEMODULATOR 🚨
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: Extracts high-level Disk Name and IDs from the cached Track 18, Sector 0 buffer [1.1].
  - **`list_directory()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: Traces standard 1541 directory linkages from the demodulated sector caches.
  - **`extract_file_bytes()`** [CORE / MODE-AGNOSTIC] *(Bound to `G64FileSystemPlugin` instance)*: Sequentially follows a file's track and sector link chain from our demodulated

---

## 📄 `src/02_drivers_commodore/03_d71.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `D71FileSystemPlugin` *(Inherits: `BaseVFSHandler`)*
  - **`get_d71_linear_sector_index()`** [CORE / MODE-AGNOSTIC] *(Bound to `D71FileSystemPlugin` instance)*: Fact-aligned 1571 sector accumulator mapping 70 tracks to linear array slots.
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `D71FileSystemPlugin` instance)*: No external parameters.
  - **`check_sector_free_status()`** [CORE / MODE-AGNOSTIC] *(Bound to `D71FileSystemPlugin` instance)*: Natively checks your live Side 0 and Side 1 allocation bitmasks to identify
  - **`toggle_sector_allocation_status()`** [CORE / MODE-AGNOSTIC] *(Bound to `D71FileSystemPlugin` instance)*: Natively flips the allocation bit mask for a 1571 double-sided .d71 image
  - **`write_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `D71FileSystemPlugin` instance)*: Unified Flat-File Sector Writer for the 1571 plugin.
  - **`get_d71_linear_sector_offset()`** [CORE / MODE-AGNOSTIC] *(Bound to `D71FileSystemPlugin` instance)*: Params: (t, s)
  - **`list_directory()`** [CORE / MODE-AGNOSTIC] *(Bound to `D71FileSystemPlugin` instance)*: Returns the fully parsed folder directory entries list matching your exact 32-byte step buffer specs.
  - **`read_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `D71FileSystemPlugin` instance)*: Natively queries the raw .d71 payload buffer using 70-track sector offset formulas.
  - **`extract_file_bytes()`** [CORE / MODE-AGNOSTIC] *(Bound to `D71FileSystemPlugin` instance)*: Assembles raw file payload byte streams by sequentially traversing the 1571 track/sector chains.

---

## 📄 `src/02_drivers_commodore/04_d81.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `D81FileSystemPlugin`
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Params: (payload_bytes, archive_name)
  - **`get_d81_linear_sector_index()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Translates physical 1581 1-based tracks and 0-based sectors into a flat,
  - **`read_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Extracts a raw 256-byte sector payload block natively from the image stream.
  - **`write_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Production-grade high-density 1581 .d81 sector modifier with integrated
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Natively isolates unique disk metadata, splits layout IDs, and builds headers [1.1].
  - **`allocate_virtual_sector_in_bam()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Hardware-accurate bitwise allocator for 1581 profiles.
  - **`deallocate_virtual_sector_in_bam()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Hardware-accurate bitwise deallocator for 1581 profiles.
  - **`create_1581_partition_sectors()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Surgically compiles and injects standard 1581 partition sector containers.
  - **`get_partition_creation_track_matrix()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Computes a dictionary map of tracks 1-80 indicating selection eligibility
  - **`list_directory()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Traces standard 1581 directory linkages dynamically across subdirectories [1.13].
  - **`extract_file_bytes()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Sequentially extracts raw file data bytes from a 1581 filesystem structure.
  - **`check_sector_free_status()`** [CORE / MODE-AGNOSTIC] *(Bound to `D81FileSystemPlugin` instance)*: Natively checks the 1581 dual-BAM bitmasks to identify if a block is free (True)

---

## 📄 `src/02_drivers_commodore/05_lnx.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `LNXFileSystemPlugin` *(Inherits: `BaseVFSHandler`)*
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `LNXFileSystemPlugin` instance)*: No external parameters.
  - **`read_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `LNXFileSystemPlugin` instance)*: Natively queries the fake sector-buffered storage grid using standard T/S coordinates.
  - **`extract_file_bytes()`** [CORE / MODE-AGNOSTIC] *(Bound to `LNXFileSystemPlugin` instance)*: Extracts raw file payload bytes natively by walking our virtual sector chains.

---

## 📄 `src/03_drivers_cmd/01_cmd_base.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `BaseCMDFloppyPlugin` *(Inherits: `BaseVFSHandler`)*
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseCMDFloppyPlugin` instance)*: No external parameters.
  - **`navigate_forward()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseCMDFloppyPlugin` instance)*: Polymorphically builds and boots inner child driver filesystems in-memory.
  - **`write_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseCMDFloppyPlugin` instance)*: Flat-File Sector Writer for the CMD floppy master system tracks.
  - **`flush_dhd_to_disk()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseCMDFloppyPlugin` instance)*: Polymorphic File Serialization Engine for CMD Floppy Containers.
  - **`read_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `BaseCMDFloppyPlugin` instance)*: Params: (track, sector)

---

## 📄 `src/03_drivers_cmd/02_dhd.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `DHDFileSystemPlugin` *(Inherits: `BaseVFSHandler`)*
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `DHDFileSystemPlugin` instance)*: No external parameters.
  - **`flush_dhd_to_disk()`** [CORE / MODE-AGNOSTIC] *(Bound to `DHDFileSystemPlugin` instance)*: Safely serializes the entire master platter memory payload array back onto the
  - **`navigate_forward()`** [CORE / MODE-AGNOSTIC] *(Bound to `DHDFileSystemPlugin` instance)*: Intercepts active [ENTER] cursor actions on partition folder rows.
  - **`read_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `DHDFileSystemPlugin` instance)*: Redirects absolute block extractions directly into target sub-partition streams.
  - **`toggle_sector_allocation_status()`** [CORE / MODE-AGNOSTIC] *(Bound to `DHDFileSystemPlugin` instance)*: Bypasses master track allocations for direct inner partition private management passes.

---

## 📄 `src/03_drivers_cmd/03_d2m.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `D2MFileSystemPlugin` *(Inherits: `BaseCMDFloppyPlugin`)*
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `D2MFileSystemPlugin` instance)*: Params: (payload_data, archive_name)

---

## 📄 `src/03_drivers_cmd/04_d4m.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `D4MFileSystemPlugin` *(Inherits: `BaseCMDFloppyPlugin`)*
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `D4MFileSystemPlugin` instance)*: Params: (payload_data, archive_name)

---

## 📄 `src/03_drivers_cmd/05_dnp.py`

### 🧩 Classes & Instance-Bound Routines
#### Class: `DNPFileSystemPlugin` *(Inherits: `BaseVFSHandler`)*
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPFileSystemPlugin` instance)*: No external parameters.
  - **`toggle_sector_allocation_status()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPFileSystemPlugin` instance)*: Natively flips the allocation bit mask for a CMD Native .dnp partition
  - **`extract_file_bytes()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPFileSystemPlugin` instance)*: Params: (vfs_meta_node)
  - **`navigate_forward()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPFileSystemPlugin` instance)*: Params: (track, sector, name)
  - **`navigate_backward()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPFileSystemPlugin` instance)*: No external parameters.
  - **`read_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPFileSystemPlugin` instance)*: Passes the sector read request straight down to the Native Partition driver.
  - **`write_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPFileSystemPlugin` instance)*: Passes the sector write execution down to the Native Partition handler,

#### Class: `DNPNativeHandler` *(Inherits: `BaseContainerHandler`)*
  - **`__init__()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: Params: (vfs_stream, total_blocks)
  - **`get_dnp_bam_matrix()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: Pure Data Engine: Parses the system BAM sectors on Track 1 (Sectors 2-33).
  - **`read_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: Params: (track, sector)
  - **`get_raw_block()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: Params: (track, sector)
  - **`mount()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: No external parameters.
  - **`allocate_free_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: High-Level Virtual Drive Allocation Guard:
  - **`find_next_free_allocation_block()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: High-Level Allocation Engine: Walks the synchronized BAM bit matrix natively
  - **`write_virtual_sector()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: Surgically overwrites a 256-byte sector payload block inside the raw DNP platter stream.
  - **`list_directory_entries()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: Params: (track, sector)
  - **`navigate_forward()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: Params: (track, sector, name)
  - **`navigate_backward()`** [CORE / MODE-AGNOSTIC] *(Bound to `DNPNativeHandler` instance)*: No external parameters.

---

## 📄 `src/07_app_runtime/00_shared_helpers.py`

### ⚙️ Standalone Routines
- **`verify_and_bootstrap_dependencies()`** [CORE / MODE-AGNOSTIC] — Natively inspects the workstation environment for mandatory external drivers.
- **`main_orchestration_loop()`** [HYBRID: PYGAME + STD] — Main baseline launch controller coordinating curses events or handing off to Pygame.

---

## 📄 `src/07_app_runtime/99_main_entry.py`

---


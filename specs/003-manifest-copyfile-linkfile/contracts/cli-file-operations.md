# CLI Contract: File Operations (Copyfile/Linkfile)

**Feature**: 003-manifest-copyfile-linkfile
**Date**: 2025-10-21

## Overview

This contract defines the command-line interface behavior for the `subrepo sync` command when processing copyfile and linkfile elements in manifests.

## Command: `subrepo sync`

### Existing Behavior (Unchanged)

The `sync` command synchronizes all projects defined in the manifest with their upstream repositories using git subtree.

### New Behavior (File Operations)

After successfully syncing each project's git subtree, the command will:
1. Process all `<copyfile>` elements for the project
2. Process all `<linkfile>` elements for the project
3. Continue processing remaining projects even if file operations fail
4. Report summary of file operations at completion

---

## Success Scenarios

### Scenario 1: Successful copyfile operations

**Command**:
```bash
subrepo sync
```

**Manifest** (excerpt):
```xml
<project name="org/core" path="components/core">
  <copyfile src="docs/README.md" dest="README.md" />
</project>
```

**Expected Output**:
```
Syncing project org/core...
  Subtree sync complete
  Copied: components/core/docs/README.md → README.md

File Operations: 1/1 succeeded
```

**Exit Code**: `0`

**Filesystem State**:
- File copied from `components/core/docs/README.md` to workspace `README.md`
- Permissions preserved from source

---

### Scenario 2: Successful linkfile operations

**Command**:
```bash
subrepo sync
```

**Manifest** (excerpt):
```xml
<project name="org/tools" path="tools">
  <linkfile src="scripts/build.sh" dest="build.sh" />
</project>
```

**Expected Output**:
```
Syncing project org/tools...
  Subtree sync complete
  Linked: build.sh → tools/scripts/build.sh

File Operations: 1/1 succeeded
```

**Exit Code**: `0`

**Filesystem State**:
- Symbolic link created at workspace `build.sh` pointing to `tools/scripts/build.sh`

---

### Scenario 3: Linkfile fallback to copy (Windows/unsupported filesystem)

**Command**:
```bash
subrepo sync
```

**Manifest** (excerpt):
```xml
<project name="org/docs" path="docs">
  <linkfile src="guide.md" dest="GUIDE.md" />
</project>
```

**Expected Output**:
```
Syncing project org/docs...
  Subtree sync complete
  Warning: Symlinks not supported, copying instead: GUIDE.md
  Copied (fallback): docs/guide.md → GUIDE.md

File Operations: 1/1 succeeded
  Symlink fallbacks: 1 (copied instead)
```

**Exit Code**: `0`

**Filesystem State**:
- File copied instead of symlinked
- Warning logged to inform user of fallback behavior

---

### Scenario 4: Multiple file operations

**Command**:
```bash
subrepo sync
```

**Manifest** (multiple projects with file operations):

**Expected Output**:
```
Syncing project org/core...
  Subtree sync complete
  Copied: components/core/docs/README.md → README.md
  Copied: components/core/config/Makefile → Makefile

Syncing project org/tools...
  Subtree sync complete
  Linked: build.sh → tools/scripts/build.sh
  Linked: test.sh → tools/scripts/test.sh

File Operations: 4/4 succeeded
```

**Exit Code**: `0`

---

## Error Scenarios

### Scenario 5: Manifest validation fails (duplicate dest paths)

**Command**:
```bash
subrepo sync
```

**Manifest** (invalid - duplicate dest):
```xml
<project name="org/core" path="components/core">
  <copyfile src="docs/README.md" dest="README.md" />
</project>
<project name="org/utils" path="components/utils">
  <copyfile src="guide/README.md" dest="README.md" />
</project>
```

**Expected Output**:
```
Error: Invalid manifest
Duplicate copyfile destination 'README.md': conflicts between projects 'org/core' and 'org/utils'
```

**Exit Code**: `1`

**Filesystem State**: No changes made

---

### Scenario 6: Source file does not exist

**Command**:
```bash
subrepo sync
```

**Manifest** (copyfile with non-existent src):
```xml
<project name="org/core" path="components/core">
  <copyfile src="nonexistent.txt" dest="file.txt" />
</project>
```

**Expected Output**:
```
Syncing project org/core...
  Subtree sync complete
  Error: Failed to copy file: components/core/nonexistent.txt not found

File Operations: 0/1 succeeded
  Failed: 1

Failures:
  - org/core (copyfile): nonexistent.txt → file.txt: Source file not found
```

**Exit Code**: `1`

**Filesystem State**: Subtree synced, but file not copied

---

### Scenario 7: Path security violation (directory traversal)

**Command**:
```bash
subrepo sync
```

**Manifest** (malicious path with ".."):
```xml
<project name="org/evil" path="evil">
  <copyfile src="../../../etc/passwd" dest="passwd" />
</project>
```

**Expected Output**:
```
Syncing project org/evil...
  Subtree sync complete
  Error: Security violation: Source path contains '..' components: ../../../etc/passwd

File Operations: 0/1 succeeded
  Failed: 1

Failures:
  - org/evil (copyfile): ../../../etc/passwd → passwd: Path security violation
```

**Exit Code**: `1`

**Filesystem State**: No files copied

---

### Scenario 8: Destination already exists as directory

**Command**:
```bash
subrepo sync
```

**Precondition**: Directory `README.md/` exists in workspace

**Manifest**:
```xml
<project name="org/core" path="components/core">
  <copyfile src="docs/README.md" dest="README.md" />
</project>
```

**Expected Output**:
```
Syncing project org/core...
  Subtree sync complete
  Error: Cannot copy file: destination 'README.md' exists as a directory

File Operations: 0/1 succeeded
  Failed: 1

Failures:
  - org/core (copyfile): docs/README.md → README.md: Destination is a directory
```

**Exit Code**: `1`

---

### Scenario 9: Multiple failures continue processing

**Command**:
```bash
subrepo sync
```

**Manifest** (multiple projects, some fail):
```xml
<project name="org/good" path="good">
  <copyfile src="file.txt" dest="good.txt" />
</project>
<project name="org/bad1" path="bad1">
  <copyfile src="missing.txt" dest="bad1.txt" />
</project>
<project name="org/bad2" path="bad2">
  <linkfile src="../../etc/passwd" dest="bad2.txt" />
</project>
```

**Expected Output**:
```
Syncing project org/good...
  Subtree sync complete
  Copied: good/file.txt → good.txt

Syncing project org/bad1...
  Subtree sync complete
  Error: Failed to copy file: bad1/missing.txt not found

Syncing project org/bad2...
  Subtree sync complete
  Error: Security violation: Source path contains '..' components: ../../etc/passwd

File Operations: 1/3 succeeded
  Failed: 2

Failures:
  - org/bad1 (copyfile): missing.txt → bad1.txt: Source file not found
  - org/bad2 (linkfile): ../../etc/passwd → bad2.txt: Path security violation
```

**Exit Code**: `1`

**Filesystem State**: Only successful operation (org/good) completed

---

### Scenario 10: Permission denied

**Command**:
```bash
subrepo sync
```

**Precondition**: Destination directory is read-only

**Manifest**:
```xml
<project name="org/core" path="core">
  <copyfile src="file.txt" dest="output/file.txt" />
</project>
```

**Expected Output**:
```
Syncing project org/core...
  Subtree sync complete
  Error: Permission denied: Cannot write to output/file.txt

File Operations: 0/1 succeeded
  Failed: 1

Failures:
  - org/core (copyfile): file.txt → output/file.txt: Permission denied
```

**Exit Code**: `1`

---

## Output Format Specification

### Progress Messages (during sync)

Format for copyfile success:
```
  Copied: <relative-src-path> → <dest-path>
```

Format for linkfile success:
```
  Linked: <dest-path> → <relative-src-path>
```

Format for linkfile fallback:
```
  Warning: Symlinks not supported, copying instead: <dest-path>
  Copied (fallback): <relative-src-path> → <dest-path>
```

Format for operation errors:
```
  Error: <error-description>
```

### Summary Section (at end of sync)

Format when all succeed:
```
File Operations: <success>/<total> succeeded
```

Format with fallbacks:
```
File Operations: <success>/<total> succeeded
  Symlink fallbacks: <count> (copied instead)
```

Format with failures:
```
File Operations: <success>/<total> succeeded
  Failed: <failed-count>

Failures:
  - <project-name> (<copyfile|linkfile>): <src> → <dest>: <error-message>
  [... more failures ...]
```

---

## Exit Codes

| Exit Code | Condition |
|-----------|-----------|
| `0` | All operations succeeded (including symlink fallbacks) |
| `1` | One or more file operations failed |
| `1` | Manifest validation failed (duplicate dest paths) |
| `1` | Path security violation detected |

---

## Environment Considerations

### Platform Detection

The command automatically detects platform capabilities:
- **Linux/macOS**: Full symlink support, no fallback needed
- **Windows with Developer Mode**: Full symlink support
- **Windows without Developer Mode**: Automatic fallback to copy with warning

No user configuration required; behavior is automatic based on platform.

### Filesystem Limitations

- **FAT32/exFAT**: No symlink support → automatic fallback to copy
- **Network filesystems**: May have limited symlink support → fallback triggered as needed
- **NTFS on Linux**: Full symlink support via ntfs-3g

---

## Testing Requirements

### Contract Test Coverage

1. **Success paths**:
   - Single copyfile operation
   - Single linkfile operation
   - Multiple operations in one project
   - Multiple projects with mixed operations
   - Linkfile fallback to copy (simulated no-symlink environment)

2. **Error paths**:
   - Manifest validation failure (duplicate dest)
   - Missing source file
   - Path security violations (.. in path)
   - Destination exists as directory
   - Permission denied scenarios
   - Multiple failures with continue-on-error behavior

3. **Output format**:
   - Progress messages match specification
   - Summary format matches specification
   - Error messages are actionable and clear

4. **Exit codes**:
   - Exit 0 on all success
   - Exit 1 on any failure
   - Exit 1 on validation error

---

## Backward Compatibility

**No breaking changes**: Manifests without `<copyfile>` or `<linkfile>` elements work exactly as before. The feature is purely additive.

**Version compatibility**: Older versions of subrepo will ignore `<copyfile>` and `<linkfile>` elements (standard XML behavior), though they won't perform the file operations.

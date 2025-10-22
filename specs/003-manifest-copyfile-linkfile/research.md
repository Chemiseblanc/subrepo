# Technical Research: copyfile and linkfile Implementation

Research conducted: 2025-10-21

This document outlines best practices for implementing copyfile and linkfile support in a Python CLI tool using only the Python 3.14+ standard library.

---

## 1. Path Security Validation

### Decision
Use `pathlib.Path.resolve()` combined with `Path.is_relative_to()` (Python 3.9+) to validate that file paths don't escape the intended workspace directory.

### Rationale
- **`resolve()`**: Converts paths to absolute canonical form, resolving all symlinks and collapsing ".." segments
- **`is_relative_to()`**: Provides a clean, explicit API for checking path containment
- This combination prevents directory traversal attacks (e.g., `../../../../etc/passwd`)
- Both methods are part of the standard library and work cross-platform

### Implementation Pattern
```python
from pathlib import Path

def validate_path_security(base_dir: Path, user_path: str) -> Path:
    """
    Validates that a user-provided path stays within the base directory.

    Args:
        base_dir: The root directory that files must stay within
        user_path: User-provided path (relative or absolute)

    Returns:
        Resolved absolute path

    Raises:
        ValueError: If path escapes base_dir
    """
    # Resolve base directory to absolute canonical form
    base_resolved = base_dir.resolve()

    # Combine and resolve the user path
    target_resolved = (base_resolved / user_path).resolve()

    # Security check: ensure path is still inside base_dir
    if not target_resolved.is_relative_to(base_resolved):
        raise ValueError(
            f"Path '{user_path}' attempts to escape workspace directory"
        )

    return target_resolved
```

### Alternatives Considered

1. **String prefix checking** (`str.startswith()`)
   - Less robust, can be bypassed with symlinks
   - String comparison doesn't handle path normalization

2. **Checking `.parents` attribute**
   ```python
   if base_resolved not in target_resolved.parents:
       raise ValueError("Invalid path")
   ```
   - More verbose than `is_relative_to()`
   - Functionally equivalent but less readable

3. **Manual path component analysis**
   - Error-prone, reinvents the wheel
   - Doesn't handle edge cases properly

### Important Security Considerations

1. **Symlink following**: `resolve()` follows all symlinks by default. This is generally desired for security validation, but be aware that if an attacker can create symlinks within the base directory, they might link to files outside it.

2. **TOCTOU (Time-of-check-time-of-use)**: There's a race condition between validation and file operation. Minimize the window by performing operations immediately after validation.

3. **Strict mode**: `resolve(strict=True)` raises `FileNotFoundError` if the path doesn't exist. For copyfile/linkfile operations, you may want to validate the source with `strict=True` and destination with `strict=False`.

### Code Patterns

**Module**: `pathlib`

**Key Functions**:
- `Path.resolve(strict=False)`: Resolve to absolute path
- `Path.is_relative_to(other)`: Check path containment (Python 3.9+)

---

## 2. Cross-Platform Symlink Handling

### Decision
Implement a graceful fallback strategy: attempt to create symlinks, but fall back to file copying on platforms where symlink creation fails. Provide clear user feedback about the fallback.

### Rationale
- Windows symlink support is inconsistent:
  - Requires administrator privileges (or Developer Mode on Windows 10+)
  - Raises `OSError` with `errno.EPERM` when privileges are insufficient
- Linux and macOS have native symlink support with no special privileges required
- Falling back to copy ensures the tool works in all environments
- Informing users about the fallback maintains transparency

### Implementation Pattern

```python
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def create_link_or_copy(src: Path, dst: Path, *, force_copy: bool = False) -> str:
    """
    Create a symbolic link from dst to src. Fall back to copying if symlinks
    are not supported.

    Args:
        src: Source file path (link target)
        dst: Destination link path
        force_copy: If True, skip symlink attempt and copy directly

    Returns:
        "symlink" if symbolic link was created, "copy" if file was copied

    Raises:
        OSError: If both symlink and copy operations fail
    """
    # Ensure parent directory exists
    dst.parent.mkdir(parents=True, exist_ok=True)

    if force_copy:
        shutil.copy2(src, dst)
        return "copy"

    try:
        # Attempt to create symbolic link
        os.symlink(src, dst, target_is_directory=src.is_dir())
        return "symlink"
    except OSError as e:
        # Handle permission errors on Windows
        if e.errno == 1314:  # ERROR_PRIVILEGE_NOT_HELD on Windows
            logger.warning(
                f"Insufficient privileges to create symlink {dst} -> {src}. "
                f"Falling back to file copy. "
                f"Enable Developer Mode or run as administrator for symlink support."
            )
        elif e.errno == 19 or e.errno == 38:  # ENODEV: No symlink support
            logger.info(
                f"Filesystem does not support symlinks. Copying {src} to {dst}."
            )
        else:
            # Other errors might indicate real problems
            logger.warning(
                f"Failed to create symlink {dst} -> {src}: {e}. "
                f"Falling back to file copy."
            )

        # Fallback: copy the file
        shutil.copy2(src, dst)
        return "copy"
    except NotImplementedError:
        # Some platforms may not implement os.symlink
        logger.info("Symlinks not supported on this platform. Using file copy.")
        shutil.copy2(src, dst)
        return "copy"


def check_symlink_support() -> bool:
    """
    Test whether the current platform and user permissions support symlink creation.

    Returns:
        True if symlinks can be created, False otherwise
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        src = tmppath / "test_src.txt"
        link = tmppath / "test_link.txt"

        src.write_text("test")

        try:
            os.symlink(src, link)
            return True
        except (OSError, NotImplementedError):
            return False
```

### Alternatives Considered

1. **Platform detection only** (`sys.platform == 'win32'`)
   - Not reliable: Windows 10 Developer Mode supports symlinks
   - Doesn't account for filesystem capabilities

2. **Always use file copies**
   - Loses the benefits of symlinks (space efficiency, instant updates)
   - Not suitable for large files or workflows that expect true links

3. **Fail hard when symlinks unavailable**
   - Poor user experience
   - Reduces tool compatibility

4. **Windows-specific privilege checking**
   - Complex: requires Windows API calls via `ctypes`
   - Still doesn't guarantee success (filesystem might not support symlinks)
   - Better to use try/except pattern

### Important Considerations

1. **`target_is_directory` parameter**: On Windows, `os.symlink()` requires the `target_is_directory` flag to be set correctly. Use `src.is_dir()` to determine this.

2. **Relative vs. absolute links**: Consider whether links should be relative (more portable) or absolute (more explicit). For copyfile/linkfile, relative links are typically preferred.

3. **Link verification**: After creating a link, you can verify it with:
   ```python
   if os.path.islink(dst) and os.readlink(dst) == str(src):
       # Link created successfully
   ```

4. **Windows Developer Mode**: On Windows 10+, users can enable Developer Mode to allow symlink creation without admin privileges.

### Code Patterns

**Modules**: `os`, `shutil`, `pathlib`

**Key Functions**:
- `os.symlink(src, dst, target_is_directory=False)`: Create symbolic link
- `os.path.islink(path)`: Check if path is a symbolic link
- `os.readlink(path)`: Read the target of a symbolic link
- `shutil.copy2(src, dst)`: Copy file with metadata (fallback)

**Error Codes**:
- `errno.EPERM (1)` or Windows error `1314`: Insufficient privileges
- `errno.ENODEV (19)`: No symlink support on filesystem
- `errno.EXDEV (18)`: Cross-device link (not applicable for symlinks)

---

## 3. File Copy with Permission Preservation

### Decision
Use `shutil.copy2()` for file copying to preserve as much metadata as possible, including permissions and timestamps.

### Rationale
- `shutil.copy2()` attempts to preserve all metadata the platform supports
- It never raises exceptions for metadata preservation failures, making it robust
- Handles cross-platform differences in metadata support automatically
- Part of the standard library with well-tested implementation

### Implementation Pattern

```python
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def copy_file_with_metadata(src: Path, dst: Path) -> None:
    """
    Copy a file from src to dst, preserving permissions and metadata.

    Args:
        src: Source file path
        dst: Destination file path

    Raises:
        FileNotFoundError: If src doesn't exist
        PermissionError: If insufficient permissions to read src or write dst
        OSError: For other I/O errors
    """
    # Ensure parent directory exists
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Copy file with metadata preservation
    try:
        shutil.copy2(src, dst)
        logger.debug(f"Copied {src} to {dst} with metadata preservation")
    except Exception as e:
        logger.error(f"Failed to copy {src} to {dst}: {e}")
        raise


def copy_file_minimal(src: Path, dst: Path) -> None:
    """
    Copy only file contents and permission mode, not full metadata.
    Useful when timestamp preservation is undesired.

    Args:
        src: Source file path
        dst: Destination file path
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)  # Preserves permission mode only
```

### Alternatives Considered

1. **`shutil.copyfile()`**
   - Only copies file contents, no metadata
   - Faster but loses permissions and timestamps
   - Not suitable for repository management tools

2. **`shutil.copy()`**
   - Copies contents and permission mode only
   - Doesn't preserve timestamps
   - Better than `copyfile()` but still incomplete

3. **Manual copying with metadata preservation**
   ```python
   # Copy contents
   shutil.copyfile(src, dst)
   # Copy stats
   shutil.copystat(src, dst)
   ```
   - Equivalent to `copy2()` but more verbose
   - No advantage over using `copy2()` directly

4. **Using `os.stat()` and `os.chmod()` manually**
   - Much more complex
   - Platform-specific edge cases
   - Reinvents what `shutil` already provides

### Metadata Preservation Limitations

1. **POSIX limitations**: On POSIX systems, file owner and group are NOT preserved by `copy2()`. Preserving ownership requires:
   ```python
   stat_info = os.stat(src)
   os.chown(dst, stat_info.st_uid, stat_info.st_gid)  # Requires root
   ```
   This typically requires root privileges and is not needed for most use cases.

2. **Extended attributes**: Extended attributes (xattrs) and ACLs are not preserved by `copy2()`. For complete preservation, use:
   ```python
   shutil.copy2(src, dst)
   # Extended attributes (Linux)
   import subprocess
   subprocess.run(['cp', '--preserve=all', str(src), str(dst)])
   ```
   However, this requires external tools and is platform-specific.

3. **Windows-specific metadata**: On Windows, `copy2()` preserves basic file attributes but not all NTFS-specific metadata.

### Code Patterns

**Module**: `shutil`

**Key Functions**:
- `shutil.copy2(src, dst)`: Copy with metadata preservation (recommended)
- `shutil.copy(src, dst)`: Copy with permission mode only
- `shutil.copyfile(src, dst)`: Copy contents only (no metadata)
- `shutil.copystat(src, dst)`: Copy metadata only (requires file exists)

**Comparison**:
| Function | Contents | Permissions | Timestamps | Owner/Group |
|----------|----------|-------------|------------|-------------|
| `copyfile()` | Yes | No | No | No |
| `copy()` | Yes | Yes | No | No |
| `copy2()` | Yes | Yes | Yes* | No |

*Timestamps preserved on best-effort basis

---

## 4. Atomic File Operations

### Decision
Use the "write to temporary file, then atomic rename" pattern with `tempfile.NamedTemporaryFile(delete=False)` and `os.replace()`.

### Rationale
- Atomic renames prevent partial writes and race conditions
- `os.replace()` is cross-platform and atomic on both POSIX and Windows
- Temporary files in the same directory ensure same-filesystem operation
- Standard library provides all necessary tools
- Protects against crashes, interruptions, and concurrent access

### Implementation Pattern

```python
import os
import tempfile
from pathlib import Path
from typing import Callable

def atomic_write(
    dst: Path,
    write_func: Callable[[Path], None],
    *,
    preserve_mode: bool = True
) -> None:
    """
    Atomically write to a file using a temporary file and rename.

    Args:
        dst: Destination file path
        write_func: Function that writes to the provided path
        preserve_mode: If True and dst exists, preserve its permission mode

    Raises:
        OSError: If write or rename operation fails

    Example:
        atomic_write(
            Path('/path/to/file.txt'),
            lambda p: p.write_text('content')
        )
    """
    # Ensure parent directory exists
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Preserve existing file mode if requested
    original_mode = None
    if preserve_mode and dst.exists():
        original_mode = dst.stat().st_mode

    # Create temporary file in same directory for atomic rename
    # (rename is only atomic within same filesystem)
    fd = None
    tmp_path = None

    try:
        # Create temporary file in same directory
        fd, tmp_name = tempfile.mkstemp(
            dir=dst.parent,
            prefix=f".{dst.name}.",
            suffix=".tmp"
        )
        tmp_path = Path(tmp_name)

        # Close the file descriptor - we'll use Path API
        os.close(fd)
        fd = None

        # Call user's write function
        write_func(tmp_path)

        # Preserve original mode if requested
        if original_mode is not None:
            tmp_path.chmod(original_mode)

        # Atomic replace (overwrites on both POSIX and Windows)
        os.replace(tmp_path, dst)
        tmp_path = None  # Successfully renamed, don't clean up

    finally:
        # Clean up on error
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass

        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def atomic_copy(src: Path, dst: Path) -> None:
    """
    Atomically copy a file using temporary file and rename.

    Args:
        src: Source file path
        dst: Destination file path
    """
    import shutil

    def write_copy(tmp: Path) -> None:
        shutil.copy2(src, tmp)

    atomic_write(dst, write_copy, preserve_mode=False)
```

### Alternatives Considered

1. **Direct write without temporary file**
   - Not atomic: file can be corrupted if operation is interrupted
   - Multiple readers might see partial writes
   - Unacceptable for critical operations

2. **Using `os.rename()` instead of `os.replace()`**
   - Fails on Windows if destination exists
   - Requires platform-specific code
   - `os.replace()` is the modern, cross-platform solution

3. **Using `NamedTemporaryFile(delete=True)`**
   - File gets deleted on close, preventing rename
   - Must use `delete=False` for atomic rename pattern

4. **Hard link approach** (`os.link()`)
   ```python
   # Write to temp file
   # Create hard link to final name
   os.link(tmp_path, dst)
   ```
   - Doesn't work if destination already exists
   - Platform-specific limitations
   - More complex than rename approach

5. **Using `shutil.move()`**
   - Not atomic across filesystems (copies then deletes)
   - `os.replace()` is more explicit and guaranteed atomic

### Important Considerations

1. **Same filesystem requirement**: Atomic renames only work within the same filesystem. Always create the temporary file in the same directory as the destination:
   ```python
   # Correct - same directory
   tempfile.mkstemp(dir=dst.parent)

   # Wrong - might be different filesystem
   tempfile.mkstemp()  # Uses /tmp or similar
   ```

2. **Error handling**: Always clean up temporary files in a `finally` block to avoid leaving orphaned temp files.

3. **Permission preservation**: If replacing an existing file, consider preserving its permissions:
   ```python
   if dst.exists():
       original_mode = dst.stat().st_mode
       # ... write to tmp ...
       tmp_path.chmod(original_mode)
   ```

4. **Atomic directory operations**: This pattern doesn't work for directories. Directory creation is not atomic.

### Cross-Platform Behavior

**`os.replace(src, dst)`**:
- **POSIX**: Atomically replaces destination if it exists
- **Windows**: Atomically replaces destination if it exists (uses `MoveFileEx` with `MOVEFILE_REPLACE_EXISTING`)
- **Atomicity**: Guaranteed atomic on both platforms
- **Cross-filesystem**: Fails if src and dst are on different filesystems

**`os.rename(src, dst)`**:
- **POSIX**: Atomic, replaces destination
- **Windows**: Raises `FileExistsError` if destination exists
- **Recommendation**: Use `os.replace()` for cross-platform code

### Code Patterns

**Modules**: `tempfile`, `os`, `pathlib`

**Key Functions**:
- `tempfile.mkstemp(dir=None, prefix='', suffix='')`: Create temp file, returns (fd, path)
- `tempfile.NamedTemporaryFile(delete=False, dir=None)`: Alternative temp file creation
- `os.replace(src, dst)`: Atomic rename (Python 3.3+, recommended)
- `os.rename(src, dst)`: Atomic rename (POSIX only for overwrites)
- `Path.stat().st_mode`: Get file permissions
- `Path.chmod(mode)`: Set file permissions

**Pattern Template**:
```python
# 1. Create temp file in target directory
fd, tmp = tempfile.mkstemp(dir=target.parent)
os.close(fd)

# 2. Write to temp file
# ... write operations ...

# 3. Atomic replace
os.replace(tmp, target)
```

---

## 5. XML Parsing Patterns

### Decision
Use `xml.etree.ElementTree` with direct iteration over child elements. Use `findall()` for filtered queries and `iter()` for recursive traversal.

### Rationale
- `xml.etree.ElementTree` is part of the standard library
- Simple, well-documented API suitable for manifest files
- Efficient enough for typical manifest file sizes
- Supports both direct child access and XPath-like queries
- No external dependencies required

### Implementation Pattern

```python
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

def parse_manifest_copyfile(manifest_path: Path) -> List[dict]:
    """
    Parse copyfile elements from a manifest XML file.

    Expected XML structure:
        <project name="foo" path="bar">
            <copyfile src="source.txt" dest="destination.txt"/>
            <copyfile src="other.txt" dest="target.txt"/>
        </project>

    Args:
        manifest_path: Path to manifest XML file

    Returns:
        List of dicts with keys: 'project_name', 'project_path', 'src', 'dest'
    """
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    copyfiles = []

    # Iterate through all project elements
    for project in root.findall('project'):
        project_name = project.get('name', '')
        project_path = project.get('path', '')

        # Iterate through direct child copyfile elements
        for copyfile in project.findall('copyfile'):
            src = copyfile.get('src')
            dest = copyfile.get('dest')

            if src is None or dest is None:
                raise ValueError(
                    f"copyfile element missing required attributes in {project_name}: "
                    f"src={src}, dest={dest}"
                )

            copyfiles.append({
                'project_name': project_name,
                'project_path': project_path,
                'src': src,
                'dest': dest,
            })

    return copyfiles


def parse_manifest_linkfile(root_element: ET.Element) -> List[dict]:
    """
    Parse linkfile elements from manifest root element.

    Args:
        root_element: Root element of parsed manifest

    Returns:
        List of dicts with linkfile information
    """
    linkfiles = []

    # Find all project elements with linkfile children
    for project in root_element.iter('project'):
        project_name = project.get('name', '')
        project_path = project.get('path', '')

        # Direct children only (not recursive)
        for linkfile in project.findall('linkfile'):
            src = linkfile.get('src')
            dest = linkfile.get('dest')

            if src and dest:
                linkfiles.append({
                    'project_name': project_name,
                    'project_path': project_path,
                    'src': src,
                    'dest': dest,
                })

    return linkfiles


def safe_xml_parse(xml_path: Path) -> ET.Element:
    """
    Safely parse an XML file with error handling.

    Args:
        xml_path: Path to XML file

    Returns:
        Root element of parsed XML

    Raises:
        FileNotFoundError: If XML file doesn't exist
        ET.ParseError: If XML is malformed
    """
    try:
        tree = ET.parse(xml_path)
        return tree.getroot()
    except ET.ParseError as e:
        raise ET.ParseError(
            f"Failed to parse XML file {xml_path}: {e}"
        ) from e
```

### Alternatives Considered

1. **Using `xml.dom.minidom`**
   - More verbose API
   - Higher memory usage
   - Less Pythonic than ElementTree
   - No significant advantages for this use case

2. **Using `xml.sax`**
   - Event-driven parsing
   - More complex for simple use cases
   - Better for very large files (streaming)
   - Overkill for manifest files

3. **Using `lxml`**
   - External dependency (violates standard library requirement)
   - More features but not needed here
   - Better XPath support, but ElementTree is sufficient

4. **Manual XML parsing with regex**
   - Extremely error-prone
   - Doesn't handle XML edge cases
   - Never recommended for XML parsing

### Key ElementTree Patterns

**Direct child iteration**:
```python
# Iterate only direct children with tag 'copyfile'
for child in element.findall('copyfile'):
    # Process child
    pass
```

**Recursive iteration**:
```python
# Iterate all descendants with tag 'copyfile'
for node in element.iter('copyfile'):
    # Process node
    pass
```

**XPath-like queries**:
```python
# Find grandchildren: project/copyfile
for cf in root.findall('./project/copyfile'):
    pass

# Find all copyfile elements anywhere in tree
for cf in root.findall('.//copyfile'):
    pass

# Find with attribute filter
for cf in root.findall(".//copyfile[@dest='target.txt']"):
    pass
```

**Attribute access**:
```python
# Get attribute, returns None if not present
src = element.get('src')

# Get attribute with default value
src = element.get('src', 'default.txt')

# Get attribute, raise KeyError if not present
src = element.attrib['src']
```

### Important Considerations

1. **XPath limitations**: ElementTree supports a limited subset of XPath. For complex queries, consider upgrading to `lxml` (external dependency) or writing custom filtering logic.

2. **Namespace handling**: If the XML uses namespaces, you need to specify them in queries:
   ```python
   namespaces = {'ns': 'http://example.com/namespace'}
   for project in root.findall('ns:project', namespaces):
       pass
   ```

3. **Concurrent modification**: Don't modify the tree structure while iterating. Collect elements first, then modify:
   ```python
   # Correct
   to_remove = list(root.findall('copyfile'))
   for elem in to_remove:
       root.remove(elem)

   # Wrong - concurrent modification
   for elem in root.findall('copyfile'):
       root.remove(elem)  # May skip elements
   ```

4. **Memory efficiency**: For very large XML files (>100MB), consider using `iterparse()` for streaming:
   ```python
   for event, elem in ET.iterparse(xml_path, events=('start', 'end')):
       if event == 'end' and elem.tag == 'project':
           # Process project
           elem.clear()  # Free memory
   ```

5. **Error handling**: Always wrap XML parsing in try/except for `ParseError`:
   ```python
   try:
       tree = ET.parse(xml_path)
   except ET.ParseError as e:
       # Handle malformed XML
       pass
   ```

### Performance Comparison

| Method | Use Case | Performance |
|--------|----------|-------------|
| `element.findall('tag')` | Find direct children | O(n) where n = number of children |
| `element.iter('tag')` | Find all descendants | O(n) where n = number of descendants |
| `element.find('tag')` | Find first direct child | O(n) but stops at first match |
| Direct iteration | Access all children | O(n) |

### Code Patterns

**Module**: `xml.etree.ElementTree`

**Key Functions**:
- `ET.parse(source)`: Parse XML file, returns ElementTree
- `tree.getroot()`: Get root element
- `element.findall(match)`: Find direct children matching tag/path
- `element.find(match)`: Find first direct child
- `element.iter(tag=None)`: Recursively iterate descendants
- `element.get(key, default=None)`: Get attribute value
- `element.attrib`: Dict of all attributes
- `element.tag`: Element tag name
- `element.text`: Text content of element

**Error Handling**:
- `xml.etree.ElementTree.ParseError`: Raised for malformed XML

---

## Summary and Recommendations

### Recommended Technology Stack

| Requirement | Module | Primary Functions |
|-------------|--------|-------------------|
| Path validation | `pathlib` | `Path.resolve()`, `Path.is_relative_to()` |
| Symlink operations | `os` | `os.symlink()`, `os.path.islink()` |
| File copying | `shutil` | `shutil.copy2()` |
| Atomic operations | `tempfile`, `os` | `tempfile.mkstemp()`, `os.replace()` |
| XML parsing | `xml.etree.ElementTree` | `ET.parse()`, `Element.findall()` |

### Implementation Workflow

For implementing copyfile support:
1. Parse manifest with `xml.etree.ElementTree`
2. Validate paths with `Path.resolve()` and `is_relative_to()`
3. Use atomic operations pattern with `tempfile` + `os.replace()`
4. Copy with `shutil.copy2()` for metadata preservation

For implementing linkfile support:
1. Parse manifest with `xml.etree.ElementTree`
2. Validate paths with `Path.resolve()` and `is_relative_to()`
3. Attempt `os.symlink()`, fall back to `shutil.copy2()` on failure
4. Log the fallback action for user awareness

### Key Security Principles

1. **Always validate paths** before any file operation
2. **Use atomic operations** to prevent inconsistent states
3. **Handle errors gracefully** with appropriate fallbacks
4. **Log security-relevant decisions** (symlink fallbacks, path validation failures)
5. **Never trust user input** - always resolve and validate paths

### Testing Considerations

When testing these implementations:

1. **Path security**: Test with paths containing "..", symlinks, absolute paths
2. **Cross-platform**: Test on Windows, Linux, macOS if possible
3. **Permissions**: Test with insufficient permissions (non-admin on Windows)
4. **Atomicity**: Test interruptions (though difficult to simulate)
5. **XML parsing**: Test with malformed XML, missing attributes, namespaces
6. **Edge cases**: Empty files, large files, special characters in filenames

### References

- Python pathlib documentation: https://docs.python.org/3/library/pathlib.html
- Python shutil documentation: https://docs.python.org/3/library/shutil.html
- Python tempfile documentation: https://docs.python.org/3/library/tempfile.html
- Python xml.etree.ElementTree documentation: https://docs.python.org/3/library/xml.etree.elementtree.html
- Python os documentation: https://docs.python.org/3/library/os.html

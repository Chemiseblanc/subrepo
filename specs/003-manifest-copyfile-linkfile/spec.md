# Feature Specification: Manifest Copyfile and Linkfile Support

**Feature Branch**: `003-manifest-copyfile-linkfile`
**Created**: 2025-10-21
**Status**: Draft
**Input**: User description: "the copyfile and linkfile parts of the git-repo manifest shall be supported"

## Clarifications

### Session 2025-10-21

- Q: When multiple projects specify copyfile/linkfile elements with the same destination path, how should the system resolve this conflict? → A: Fail-fast: Report error during manifest validation, refuse to proceed with sync until conflict is resolved
- Q: When a copyfile or linkfile operation fails during sync (e.g., permission denied, disk space full, filesystem doesn't support symlinks), should the entire sync operation fail or continue processing remaining projects? → A: Continue-with-errors: Complete sync for all projects, collect and report all copyfile/linkfile failures at the end with non-zero exit code
- Q: When re-sync encounters an existing symlink at a destination path (created by a previous linkfile operation), what should happen? → A: Update: Remove existing symlink and recreate it pointing to current src path
- Q: When a copyfile element specifies a src path that points to a symlink within the project (rather than a regular file), what should happen? → A: Dereference: Follow the symlink and copy the target file content to destination
- Q: On filesystems that don't support symbolic links (e.g., Windows without developer mode, certain network filesystems), how should linkfile operations be handled? → A: Fallback-to-copy: Copy the file content instead of creating symlink, log a warning about the fallback behavior

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Copy Project Files to Workspace Root (Priority: P1)

Users need to place configuration files, build scripts, or documentation from component repositories into the workspace root directory during synchronization. For example, a component might provide a Makefile, README, or CI configuration that should be accessible at the top level of the workspace.

**Why this priority**: This is the core functionality - without copyfile support, users cannot automatically distribute files from components to the workspace root, which is a fundamental git-repo manifest feature.

**Independent Test**: Can be fully tested by creating a manifest with copyfile elements, running sync, and verifying that specified files are copied from project directories to their destination paths in the workspace.

**Acceptance Scenarios**:

1. **Given** a manifest with a project containing a copyfile element specifying src="docs/README.md" and dest="README.md", **When** the user runs sync, **Then** the README.md file from the project's docs directory is copied to the workspace root
2. **Given** a manifest with multiple copyfile elements in a single project, **When** the user runs sync, **Then** all specified files are copied to their respective destinations
3. **Given** a copyfile destination path with non-existent parent directories (e.g., dest="config/build/Makefile"), **When** sync runs, **Then** the parent directories are automatically created and the file is copied successfully

---

### User Story 2 - Create Symlinks to Project Files (Priority: P1)

Users need to create symbolic links from the workspace root to files or directories within component repositories, allowing workspace-level access to component resources without duplication. This is useful for documentation, shared configuration, or development tools that should remain synchronized with the component.

**Why this priority**: Linkfile provides an alternative to copying that keeps files synchronized with their source and saves disk space, equally important to copyfile for complete git-repo compatibility.

**Independent Test**: Can be fully tested by creating a manifest with linkfile elements, running sync, and verifying that symbolic links are created pointing to the correct source files within project directories.

**Acceptance Scenarios**:

1. **Given** a manifest with a project containing a linkfile element specifying src="scripts/build.sh" and dest="build.sh", **When** the user runs sync, **Then** a symbolic link is created at the workspace root pointing to the build.sh file in the project's scripts directory
2. **Given** a linkfile pointing to a directory (src="docs" dest="documentation"), **When** sync runs, **Then** a symbolic link to the directory is created successfully
3. **Given** a linkfile with destination path requiring parent directories, **When** sync runs, **Then** parent directories are created and the symbolic link is established
4. **Given** a linkfile element on a filesystem that doesn't support symlinks, **When** sync runs, **Then** the file content is copied to the destination and a warning is logged about the fallback behavior

---

### User Story 3 - Update Copied and Linked Files on Re-sync (Priority: P2)

When users re-synchronize their workspace after component updates, any copyfile or linkfile elements should be refreshed to reflect the latest source content. Copied files should be overwritten if the source has changed, and symlinks should remain valid.

**Why this priority**: Ensures workspace consistency after updates, but the initial sync capability (P1) provides the core value.

**Independent Test**: Can be tested by running initial sync, modifying source files in components, running sync again, and verifying that copied files are updated and symlinks still point to current sources.

**Acceptance Scenarios**:

1. **Given** a workspace with previously copied files via copyfile, **When** the source file in the component is updated and sync runs again, **Then** the destination file is overwritten with the new content
2. **Given** a workspace with existing symlinks via linkfile, **When** sync runs after component updates, **Then** the existing symlinks are removed and recreated to ensure they point to the correct current source locations
3. **Given** a linkfile element where the src path has changed in the manifest, **When** sync runs, **Then** the existing symlink is removed and recreated pointing to the new src path
4. **Given** a manifest where a copyfile element is removed, **When** sync runs, **Then** the previously copied file remains in the workspace (no automatic cleanup)

---

### User Story 4 - Handle File Operation Errors Gracefully (Priority: P2)

When copyfile or linkfile operations encounter errors (permission issues, invalid paths, conflicting files), users receive clear error messages identifying the problem and which project element caused it. The sync operation continues processing remaining projects and reports all failures at completion with a non-zero exit code.

**Why this priority**: Error handling improves user experience but is secondary to core functionality.

**Independent Test**: Can be tested by creating manifests with invalid copyfile/linkfile elements (paths outside workspace, permission-denied destinations, etc.) and verifying appropriate error messages are displayed and sync completes with all errors reported.

**Acceptance Scenarios**:

1. **Given** a copyfile element with src path pointing outside the project directory (e.g., src="../../../etc/passwd"), **When** sync runs, **Then** an error is reported, the operation is rejected for security reasons, and sync continues with remaining projects
2. **Given** a linkfile element with dest path pointing outside the workspace root, **When** sync runs, **Then** an error is reported, the symlink is not created, and sync continues with remaining projects
3. **Given** a copyfile where the source file does not exist in the project, **When** sync runs, **Then** a clear error message identifies the missing file and project, and sync continues with remaining projects
4. **Given** a destination path that already exists as a directory when a file is expected, **When** sync runs, **Then** an error is reported indicating the conflict, and sync continues with remaining projects
5. **Given** multiple copyfile/linkfile failures across different projects, **When** sync completes, **Then** all failures are reported in a summary with non-zero exit code

---

### Edge Cases

- What happens when copyfile src path does not exist in the synced project?
- What happens when copyfile dest path already exists and is a directory instead of a file?
- What happens when linkfile attempts to create a symlink outside the workspace root?
- What happens when multiple projects specify copyfile/linkfile with the same dest path (conflict)? → Manifest validation fails with clear error listing conflicting projects and destination path
- What happens when intermediate symlinks exist in the dest path (security concern)?
- What happens when the source file for a copyfile is a symlink itself? → The symlink is dereferenced and the target file content is copied to the destination
- What happens when file copy operations fail due to insufficient disk space?
- What happens when symlink creation fails on filesystems that don't support symlinks (e.g., Windows without developer mode)? → The system falls back to copying the file content and logs a warning about the fallback behavior

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST parse copyfile elements from the manifest XML as children of project elements
- **FR-002**: System MUST parse linkfile elements from the manifest XML as children of project elements
- **FR-003**: System MUST validate that copyfile src and dest attributes specify file paths (not directories or symlinks)
- **FR-004**: System MUST validate that linkfile src and dest attributes are provided and non-empty
- **FR-005**: System MUST reject copyfile/linkfile src paths that reference locations outside the project directory (no "../" escaping)
- **FR-006**: System MUST reject copyfile/linkfile dest paths that reference locations outside the workspace root
- **FR-007**: System MUST automatically create parent directories for dest paths if they do not exist
- **FR-008**: During sync operations, system MUST copy files specified in copyfile elements from project-relative src to workspace-relative dest
- **FR-008a**: When copyfile src path points to a symlink within the project, system MUST dereference the symlink and copy the target file content to the destination
- **FR-009**: During sync operations, system MUST create symbolic links specified in linkfile elements pointing from workspace-relative dest to project-relative src
- **FR-009a**: When re-syncing, system MUST remove existing symlinks at destination paths and recreate them to ensure they point to the current src path specified in the manifest
- **FR-009b**: When the filesystem does not support symbolic links, system MUST fall back to copying the file content to the destination and log a warning message indicating the fallback behavior
- **FR-010**: System MUST overwrite existing destination files when copyfile operations execute during re-sync
- **FR-011**: System MUST verify that intermediate paths in dest do not contain symlinks (security measure)
- **FR-012**: System MUST provide clear error messages when copyfile/linkfile operations fail, identifying the project and element, and MUST continue processing remaining projects rather than aborting the entire sync
- **FR-012a**: System MUST collect all copyfile/linkfile operation failures and report them in a summary at sync completion with a non-zero exit code
- **FR-013**: System MUST allow multiple copyfile and linkfile elements within a single project
- **FR-014**: System MUST allow linkfile to point to either files or directories within the project
- **FR-015**: System MUST detect and report conflicts when multiple projects specify the same dest path during manifest validation, refusing to proceed with sync until conflicts are resolved by the user
- **FR-016**: Copyfile operations MUST preserve file permissions from source to destination
- **FR-017**: System MUST execute copyfile and linkfile operations after project content is synchronized but before sync completion
- **FR-018**: System MUST validate that copyfile src files exist in the synced project before attempting to copy

### Key Entities

- **Copyfile**: Represents a file copy directive with source path (relative to project) and destination path (relative to workspace root), associated with a specific project
- **Linkfile**: Represents a symbolic link directive with source path (relative to project) and destination path (relative to workspace root), associated with a specific project
- **Project** (existing): Extended to contain zero or more copyfile and linkfile elements

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully sync workspaces containing manifests with copyfile elements, with files appearing at the specified destinations
- **SC-002**: Users can successfully sync workspaces containing manifests with linkfile elements, with functional symlinks created at the specified destinations
- **SC-003**: 100% of valid copyfile and linkfile operations specified in a manifest complete successfully during sync
- **SC-004**: Invalid copyfile/linkfile specifications (paths outside boundaries, missing sources) are detected and reported with actionable error messages before or during sync
- **SC-005**: Workspaces with complex manifests containing multiple copyfile/linkfile elements across multiple projects sync without file conflicts or data loss
- **SC-006**: Re-sync operations correctly update previously copied files to reflect source changes


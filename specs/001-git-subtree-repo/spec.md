# Feature Specification: Git Subtree Repo Manager

**Feature Branch**: `001-git-subtree-repo`
**Created**: 2025-10-18
**Status**: Draft
**Input**: User description: "Create a command line application which reimplements git-repo but instead of using multiple independant checkouts, uses git subtrees. It should support the repo manifest xml, init, and sync commands. It should also support subcommands for transparently pushing and pulling components to their own upstream as specified in the manifest."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initialize Workspace from Manifest (Priority: P1)

A developer wants to set up a new multi-repository project workspace using a single git repository with git subtrees instead of multiple independent checkouts. They have a manifest XML file that describes all the component repositories, their locations, and branch information.

**Why this priority**: This is the foundation capability - without being able to initialize a workspace from a manifest, none of the other features are usable. This is the entry point for all users.

**Independent Test**: Can be fully tested by providing a manifest XML file and verifying that the tool creates a single git repository with all specified components added as git subtrees in their correct paths, and delivers a fully functional unified repository.

**Acceptance Scenarios**:

1. **Given** a valid manifest XML file with multiple repositories, **When** user runs init command with manifest path, **Then** a new git repository is created with all components added as subtrees at specified paths
2. **Given** a manifest with branch specifications, **When** initialization completes, **Then** each subtree tracks the correct branch from its remote repository
3. **Given** an empty directory, **When** user initializes with a manifest, **Then** workspace contains a single .git directory at root (not multiple .git directories)
4. **Given** a non-empty directory, **When** user attempts initialization, **Then** system warns and prevents initialization to avoid conflicts

---

### User Story 2 - Synchronize Components (Priority: P2)

A developer working in an initialized workspace wants to update all component subtrees to match the latest commits from their remote repositories as specified in the manifest. This keeps the workspace in sync with upstream changes.

**Why this priority**: After initialization, sync is the most common operation. Developers need to regularly pull updates from upstream components to stay current with team changes.

**Independent Test**: Can be tested by initializing a workspace, making commits to upstream component repositories, then running sync and verifying all subtrees are updated to the latest commits from their respective remotes.

**Acceptance Scenarios**:

1. **Given** an initialized workspace with outdated subtrees, **When** user runs sync command, **Then** all subtrees are updated to latest commits from their tracked branches
2. **Given** a workspace where some components have local modifications, **When** sync is executed, **Then** system detects conflicts and provides clear resolution guidance
3. **Given** a manifest specifying revision/commit hashes, **When** sync runs, **Then** subtrees are updated to exact specified revisions, not latest commits
4. **Given** network connectivity issues, **When** sync attempts to fetch from remote, **Then** system reports which components failed and which succeeded

---

### User Story 3 - Push Component Changes Upstream (Priority: P3)

A developer has made changes within a subtree component and wants to push those changes back to the component's upstream repository. The tool should transparently handle the git subtree split and push operations.

**Why this priority**: Enables bidirectional workflow. While less frequent than syncing, the ability to contribute changes back to upstream components is essential for collaborative development.

**Independent Test**: Can be tested by making commits to files within a subtree path, running the push command for that component, and verifying the commits appear in the upstream repository.

**Acceptance Scenarios**:

1. **Given** commits made to files within a subtree path, **When** user runs push command for that component, **Then** changes are extracted and pushed to the component's upstream repository
2. **Given** commits spanning multiple components, **When** user pushes a specific component, **Then** only changes relevant to that component's subtree are pushed
3. **Given** a component with no local changes, **When** user attempts to push, **Then** system reports nothing to push
4. **Given** conflicts with upstream, **When** push is attempted, **Then** system detects the conflict and provides guidance for resolution

---

### User Story 4 - Pull Component Changes from Upstream (Priority: P4)

A developer wants to pull the latest changes for a specific component subtree without syncing all components. This provides granular control for updating individual components.

**Why this priority**: Provides workflow flexibility. Sometimes developers only want to update one component without pulling changes from all other components.

**Independent Test**: Can be tested by updating an upstream component repository, running the pull command for only that component, and verifying only that subtree is updated while others remain unchanged.

**Acceptance Scenarios**:

1. **Given** updates available in one component's upstream, **When** user runs pull command for that component, **Then** only that subtree is updated, other subtrees remain unchanged
2. **Given** a component name that doesn't exist in manifest, **When** user attempts to pull, **Then** system reports the component is not found in manifest
3. **Given** local modifications in the component subtree, **When** pull is attempted, **Then** system handles merge or reports conflicts appropriately
4. **Given** multiple components need updates, **When** user pulls each individually, **Then** each pull operates independently without interfering with others

---

### User Story 5 - Manage Manifest Configuration (Priority: P5)

A developer wants to view, validate, or update the manifest configuration that defines the workspace structure. This includes understanding which components are tracked and their configuration.

**Why this priority**: Supporting capability for workspace management. Useful for troubleshooting and understanding workspace composition, but not required for basic workflow.

**Independent Test**: Can be tested by running manifest commands to display current configuration, validate manifest syntax, and verify all components are properly configured.

**Acceptance Scenarios**:

1. **Given** an initialized workspace, **When** user requests manifest information, **Then** system displays all components with their paths, remotes, and branch information
2. **Given** a modified manifest file, **When** user validates it, **Then** system reports any syntax errors or invalid configurations
3. **Given** an invalid remote URL in manifest, **When** validation runs, **Then** system identifies and reports the problematic entry
4. **Given** a manifest with duplicate component paths, **When** validation occurs, **Then** system detects and reports the conflict

---

### Edge Cases

- What happens when a manifest references a component repository that no longer exists or is inaccessible?
- How does the system handle circular dependencies if manifests can reference other manifests?
- What occurs when a developer commits changes that span multiple subtree boundaries?
- How are git subtree merge commits handled to avoid cluttering the history?
- What happens when pushing to a component whose upstream has diverged significantly?
- How does the tool handle manifest updates that change component paths or remove components?
- What happens when a component's branch in the manifest is changed after initialization?
- How are binary files and large files handled across subtree operations?
- What occurs if the manifest XML is malformed or uses unsupported repo features?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST parse standard repo manifest XML format including project elements with name, path, remote, and revision attributes
- **FR-002**: System MUST support init command that creates a git repository and adds all manifest components as git subtrees
- **FR-003**: System MUST support sync command that updates all subtrees to match manifest specifications
- **FR-004**: System MUST support push command that extracts subtree commits and pushes to component's upstream repository
- **FR-005**: System MUST support pull command that updates a specific subtree from its upstream repository
- **FR-006**: System MUST maintain manifest configuration in initialized workspace for reference by subsequent commands
- **FR-007**: System MUST validate manifest XML syntax and content before performing operations
- **FR-008**: System MUST handle git subtree operations transparently without requiring users to know git subtree commands
- **FR-009**: System MUST report clear error messages when operations fail with actionable guidance for resolution
- **FR-010**: System MUST detect and warn about conflicts between local changes and upstream updates
- **FR-011**: System MUST support manifest elements for remote definitions (name and fetch URL)
- **FR-012**: System MUST support default remote and revision specifications in manifest
- **FR-013**: System MUST prevent initialization in non-empty directories to avoid conflicts
- **FR-014**: System MUST track which commits belong to which subtree for push operations
- **FR-015**: System MUST operate on the working directory's git repository without requiring specific directory structures
- **FR-016**: System MUST provide status command showing state of all components (up-to-date, ahead, behind, modified)
- **FR-017**: System MUST handle partial failures gracefully (e.g., if one component sync fails, continue with others)
- **FR-018**: System MUST support component-specific operations by name or path

### Key Entities

- **Manifest**: XML document describing workspace composition, containing remote definitions and project specifications
- **Remote**: Named git remote with fetch URL, referenced by projects in manifest
- **Project**: Component repository specification with name, path, remote reference, and revision/branch
- **Subtree**: Git subtree within the unified repository representing a project component
- **Workspace**: Single git repository containing all project subtrees, initialized from a manifest

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can initialize a workspace with 10+ components from a manifest in under 2 minutes (excluding network transfer time)
- **SC-002**: Sync operations complete with clear progress indication, reporting success/failure for each component
- **SC-003**: Push and pull operations correctly handle 100% of commits within subtree boundaries without losing changes
- **SC-004**: 95% of common repo manifest files are successfully parsed without requiring modifications
- **SC-005**: Developers can complete full workflow (init, sync, modify, push) without consulting git subtree documentation
- **SC-006**: Error messages provide sufficient information for developers to resolve issues in 90% of failure cases without external help
- **SC-007**: System detects and prevents 100% of operations that would result in data loss or corruption
- **SC-008**: Workspace uses 40-60% less disk space compared to traditional repo tool with independent checkouts (single .git directory vs multiple)
- **SC-009**: Commands complete with success/failure status codes suitable for scripting and automation
- **SC-010**: 90% of developers familiar with repo tool can successfully use basic commands (init, sync) without additional training

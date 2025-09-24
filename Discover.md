# MCP Web Discovery & Installation Implementation Plan

## Project Overview
Enhance the MCP Config Manager with web-based server discovery and automated installation capabilities, allowing users to search for, evaluate, and install MCP servers from online repositories.

## Success Criteria
- Users can search for MCP servers from web sources (Anthropic repo, Awesome lists)
- Display 5 key pieces of information for each server (name, description, author, config, install commands)
- Support three installation types: config-only, command-based, and Docker
- Maintain security through user approval workflows
- Integrate seamlessly with existing GUI and server management

---

## Phase 1: Core Backend Infrastructure (< 50K tokens)

### Task 1.1: Create Data Models (10K tokens)
- [ ] **File**: `src/mcp_config_manager/core/models/web_discovered_server.py`

```python
@dataclass
class WebDiscoveredServer:
    """Represents an MCP server discovered from web sources."""
    name: str
    description: str
    author: str
    config_content: str  # Raw JSON or TOML content
    config_type: Literal['json', 'toml']
    install_commands: List[str]
    install_type: Literal['config_only', 'command', 'docker']
    source_url: str
    source_type: Literal['github', 'awesome_list', 'other']
    confidence_score: float  # 0.0 to 1.0
    metadata: Dict[str, Any]  # Additional source-specific data

@dataclass
class InstallationResult:
    """Tracks the outcome of a server installation."""
    server: WebDiscoveredServer
    success: bool
    message: str
    installed_path: Optional[Path]
    rollback_data: Optional[Dict[str, Any]]
```

**Subtasks**:
- [ ] Define comprehensive data models with validation
- [ ] Add serialization/deserialization methods
- [ ] Create factory methods for different source types
- [ ] Add comparison and hashing for deduplication

### Task 1.2: Web Discovery Service Core (15K tokens)
- [ ] **File**: `src/mcp_config_manager/core/web_discovery_service.py`

```python
class WebDiscoveryService:
    """Service for discovering MCP servers from web sources."""

    def __init__(self):
        self.sources: List[DiscoverySource] = []
        self.cache: DiscoveryCache = DiscoveryCache()
        self.session: aiohttp.ClientSession = None

    async def search(self, query: str, sources: List[str] = None) -> List[WebDiscoveredServer]:
        """Search for MCP servers across configured sources."""

    async def get_server_details(self, server_url: str) -> WebDiscoveredServer:
        """Fetch detailed information about a specific server."""
```

**Subtasks**:
- [ ] Implement base service class with async support
- [ ] Add connection pooling and session management
- [ ] Implement caching with TTL (5 minutes default)
- [ ] Add retry logic with exponential backoff
- [ ] Create search result ranking/scoring algorithm

### Task 1.3: Source Connectors (15K tokens)
- [ ] **File**: `src/mcp_config_manager/core/discovery_sources/`

```python
class GitHubConnector(DiscoverySource):
    """Fetches MCP servers from GitHub repositories."""

    async def search(self, query: str) -> List[RawServerData]:
        """Search GitHub for MCP servers."""
        # Use GitHub REST API for search
        # Parse repository structure for MCP configs

class AwesomeListConnector(DiscoverySource):
    """Parses Awesome MCP lists for server information."""

    async def fetch_list(self, url: str) -> List[RawServerData]:
        """Parse markdown/JSON awesome lists."""
```

**Subtasks**:
- [ ] Implement GitHub API connector with authentication
- [ ] Create Markdown parser for Awesome lists
- [ ] Add JSON/YAML config extractors
- [ ] Implement README.md section parsers
- [ ] Add rate limiting and quota management

### Task 1.4: Data Extraction Engine (10K tokens)
- [ ] **File**: `src/mcp_config_manager/core/extractors/`

```python
class ConfigExtractor:
    """Extracts configuration from various file formats."""

    def extract_from_readme(self, content: str) -> Dict[str, Any]:
        """Extract config blocks from README."""

    def extract_install_commands(self, content: str) -> List[str]:
        """Extract installation instructions."""
```

**Subtasks**:
- [ ] Implement regex patterns for code block extraction
- [ ] Parse package.json, pyproject.toml, mcp.json
- [ ] Detect installation command patterns (npm, pip, docker)
- [ ] Extract author info from multiple sources
- [ ] Generate confidence scores based on extraction quality

---

## Phase 2: Installation Engine (< 40K tokens)

### Task 2.1: Installation Manager (15K tokens)
- [ ] **File**: `src/mcp_config_manager/core/web_installer.py`

```python
class WebInstaller:
    """Manages installation of discovered MCP servers."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.cli_detector = CLIDetector()

    async def install(self, server: WebDiscoveredServer,
                      target_clients: List[str],
                      user_approval: bool = True) -> InstallationResult:
        """Install a server with appropriate strategy."""
```

**Subtasks**:
- [ ] Create installation strategy selector
- [ ] Implement prerequisite checking
- [ ] Add transaction/rollback support
- [ ] Create installation queue management
- [ ] Add progress tracking with callbacks

### Task 2.2: Config-Only Installation (8K tokens)
- [ ] **File**: `src/mcp_config_manager/core/installers/config_installer.py`

```python
class ConfigOnlyInstaller:
    """Handles direct configuration injection."""

    def install(self, server: WebDiscoveredServer,
                target_clients: List[str]) -> bool:
        """Add server config to client configurations."""
```

**Subtasks**:
- [ ] Parse JSON/TOML configuration content
- [ ] Validate against MCP schema
- [ ] Merge with existing configurations
- [ ] Handle duplicate server names
- [ ] Create backup before modification

### Task 2.3: Command-Based Installation (12K tokens)
- [ ] **File**: `src/mcp_config_manager/core/installers/command_installer.py`

```python
class CommandInstaller:
    """Executes installation commands and captures configs."""

    async def install(self, server: WebDiscoveredServer,
                     working_dir: Path) -> InstallationResult:
        """Run installation commands safely."""
```

**Subtasks**:
- [ ] Validate and sanitize commands
- [ ] Check for required tools (npm, pip, etc.)
- [ ] Execute in sandboxed subprocess
- [ ] Capture and parse output
- [ ] Detect generated configuration files
- [ ] Stream logs to UI callback

### Task 2.4: Docker Installation (10K tokens)
- [ ] **File**: `src/mcp_config_manager/core/installers/docker_installer.py`

```python
class DockerInstaller:
    """Manages Docker-based MCP server installations."""

    async def install(self, server: WebDiscoveredServer,
                     install_dir: Path) -> InstallationResult:
        """Set up Docker container for MCP server."""
```

**Subtasks**:
- [ ] Check Docker availability
- [ ] Generate/locate docker-compose.yml
- [ ] Handle environment variables
- [ ] Manage container lifecycle
- [ ] Set up volume mappings
- [ ] Configure port forwarding

### Task 2.5: Security & Validation (5K tokens)
- [ ] **File**: `src/mcp_config_manager/core/security/`

```python
class InstallationSecurity:
    """Security checks for server installation."""

    def validate_source(self, server: WebDiscoveredServer) -> bool:
        """Check if source is trusted."""

    def sanitize_command(self, command: str) -> str:
        """Sanitize shell commands."""
```

**Subtasks**:
- [ ] Implement source whitelist/blacklist
- [ ] Command injection prevention
- [ ] Path traversal protection
- [ ] Resource limit enforcement
- [ ] Audit logging for all operations

---

## Phase 3: UI/UX Integration (< 50K tokens)

### Task 3.1: Enhance Discovery Dialog (15K tokens)
- [ ] **File**: `src/mcp_config_manager/gui/dialogs/discover_servers_dialog.py`

**Modifications**:
```python
class DiscoverServersDialog(QDialog):
    def _init_ui(self):
        # Add tab widget or stacked widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.local_widget, "Local Projects")
        self.tab_widget.addTab(self.web_widget, "Web Search")

    def _create_web_search_widget(self):
        # Create web search interface
```

**Subtasks**:
- [ ] Add tabbed interface for Local/Web views
- [ ] Create web search widget container
- [ ] Maintain state between tab switches
- [ ] Add keyboard navigation support
- [ ] Ensure Qt/Tk feature parity

### Task 3.2: Web Search UI Components (15K tokens)
- [ ] **File**: `src/mcp_config_manager/gui/widgets/web_search_widget.py`

```python
class WebSearchWidget(QWidget):
    """Widget for searching and displaying web MCP servers."""

    def __init__(self):
        # Search input with debouncing
        # Source filter checkboxes
        # Results table
        # Installation preview
```

**Subtasks**:
- [ ] Create search input with debounce (500ms)
- [ ] Add source selection checkboxes
- [ ] Build results table with custom item widgets
- [ ] Implement sorting and filtering
- [ ] Add pagination or infinite scroll
- [ ] Create detail preview panel

### Task 3.3: Search Result Item Widget (10K tokens)
- [ ] **File**: `src/mcp_config_manager/gui/widgets/server_search_item.py`

```python
class ServerSearchItem(QWidget):
    """Custom widget for displaying search results."""

    def __init__(self, server: WebDiscoveredServer):
        # Checkbox for selection
        # Server name with link
        # Author badge
        # Description preview
        # Install type indicator
```

**Subtasks**:
- [ ] Design visually appealing item layout
- [ ] Add expandable description
- [ ] Show confidence score indicator
- [ ] Display install type icon/badge
- [ ] Add hover effects and selection state

### Task 3.4: Installation Preview Dialog (10K tokens)
- [ ] **File**: `src/mcp_config_manager/gui/dialogs/install_preview_dialog.py`

```python
class InstallPreviewDialog(QDialog):
    """Shows detailed server info before installation."""

    def __init__(self, servers: List[WebDiscoveredServer]):
        # Config display with syntax highlighting
        # Installation commands preview
        # Target client selection
        # Security warnings
```

**Subtasks**:
- [ ] Create tabbed view for multiple servers
- [ ] Add syntax highlighting for JSON/TOML
- [ ] Show installation steps breakdown
- [ ] Display security warnings prominently
- [ ] Add proceed/cancel actions

---

## Phase 4: Controller & State Management (< 30K tokens)

### Task 4.1: Discovery Controller (10K tokens)
- [ ] **File**: `src/mcp_config_manager/gui/controllers/discovery_controller.py`

```python
class DiscoveryController:
    """Controls web discovery and installation flow."""

    def __init__(self, discovery_service: WebDiscoveryService,
                 installer: WebInstaller):
        self.discovery_service = discovery_service
        self.installer = installer

    async def search_servers(self, query: str) -> List[WebDiscoveredServer]:
        """Execute search with caching."""

    async def install_servers(self, servers: List[WebDiscoveredServer]):
        """Manage installation queue."""
```

**Subtasks**:
- [ ] Implement search request handling
- [ ] Add result caching and deduplication
- [ ] Manage installation queue
- [ ] Handle progress callbacks
- [ ] Coordinate with other controllers

### Task 4.2: Async Operations (10K tokens)
- [ ] **File**: `src/mcp_config_manager/gui/workers/discovery_worker.py`

```python
class DiscoveryWorker(QThread):
    """Background thread for discovery operations."""

    progress = pyqtSignal(int, str)
    results = pyqtSignal(list)
    error = pyqtSignal(str)
```

**Subtasks**:
- [ ] Create QThread workers for Qt
- [ ] Implement threading for Tk
- [ ] Add cancellation tokens
- [ ] Handle thread-safe updates
- [ ] Implement progress reporting

### Task 4.3: Event Integration (10K tokens)
- [ ] **Modifications to existing event system**

**Subtasks**:
- [ ] Add DISCOVERY_STARTED event
- [ ] Add INSTALLATION_PROGRESS event
- [ ] Emit SERVER_LIST_UPDATED after install
- [ ] Handle mode switching during discovery
- [ ] Integrate with backup system

---

## Phase 5: Testing & Documentation (< 30K tokens)

### Task 5.1: Unit Tests (10K tokens)
- [ ] **Files**: `tests/core/test_web_discovery.py`, `tests/core/test_web_installer.py`

**Test Coverage**:
- [ ] Discovery service with mocked responses
- [ ] Parser accuracy with real samples
- [ ] Installation strategies
- [ ] Security validation
- [ ] Error handling and rollback

### Task 5.2: Integration Tests (10K tokens)
- [ ] **File**: `tests/integration/test_web_discovery_flow.py`

**Test Scenarios**:
- [ ] End-to-end search to install
- [ ] Multi-server bulk installation
- [ ] Network failure recovery
- [ ] Cancellation mid-operation
- [ ] Conflict resolution

### Task 5.3: Documentation (10K tokens)
- [ ] **Files**:
  - [ ] `docs/features/web_discovery.md` - User guide
  - [ ] `docs/security/web_installation.md` - Security considerations
  - [ ] `docs/api/discovery_service.md` - Developer reference

**Content**:
- [ ] Feature overview and usage
- [ ] Security best practices
- [ ] Troubleshooting guide
- [ ] API documentation
- [ ] Contributing guidelines

---

## Implementation Schedule

### Week 1: Foundation
- [ ] Task 1.1: Data Models
- [ ] Task 1.2: Discovery Service Core
- [ ] Task 4.1: Discovery Controller

### Week 2: Data Sources
- [ ] Task 1.3: Source Connectors
- [ ] Task 1.4: Data Extraction Engine
- [ ] Task 5.1: Unit Tests (partial)

### Week 3: Basic Installation
- [ ] Task 2.1: Installation Manager
- [ ] Task 2.2: Config-Only Installation
- [ ] Task 2.5: Security & Validation

### Week 4: UI Foundation
- [ ] Task 3.1: Enhance Discovery Dialog
- [ ] Task 3.2: Web Search UI Components
- [ ] Task 4.2: Async Operations

### Week 5: Advanced Installation
- [ ] Task 2.3: Command-Based Installation
- [ ] Task 2.4: Docker Installation
- [ ] Task 3.3: Search Result Item Widget

### Week 6: Polish & Testing
- [ ] Task 3.4: Installation Preview Dialog
- [ ] Task 4.3: Event Integration
- [ ] Task 5.2: Integration Tests
- [ ] Task 5.3: Documentation

---

## Technical Decisions

### Architecture Patterns
- **Service Layer**: Separate business logic from UI
- **Strategy Pattern**: For different installation types
- **Observer Pattern**: For progress updates
- **Repository Pattern**: For data source abstraction

### Technology Stack
- **Networking**: aiohttp for async HTTP, requests as fallback
- **Parsing**: Beautiful Soup for HTML, markdown for MD files
- **Security**: subprocess with shell=False, command whitelisting
- **Caching**: In-memory with TTL, disk cache for offline

### Security Measures
1. All commands shown to user before execution
2. Whitelist of trusted sources (overrideable)
3. Sandboxed execution environment
4. No automatic privileged operations
5. Audit log of all installations

### Performance Targets
- Search results within 2 seconds
- Installation preview within 500ms
- Parallel installation support
- Offline cache for repeated searches
- Incremental result loading

---

## Risk Mitigation

### Technical Risks
- **API Rate Limits**: Implement caching and backoff
- **Malformed Data**: Robust parsing with fallbacks
- **Installation Failures**: Rollback mechanism
- **Network Issues**: Offline mode with cache

### Security Risks
- **Malicious Commands**: Preview and whitelist
- **Supply Chain**: Source verification
- **Data Injection**: Input sanitization
- **Resource Exhaustion**: Limits and timeouts

### UX Risks
- **Complexity**: Progressive disclosure
- **Performance**: Async operations
- **Errors**: Clear messaging
- **Trust**: Transparency in operations

---

## Success Metrics
- Search success rate > 90%
- Installation success rate > 85%
- User approval rating > 4/5
- Zero security incidents
- < 3 second search response time

---

## Notes for Implementation

1. Start with read-only operations (search, preview)
2. Implement config-only installation first (safest)
3. Add command execution after thorough testing
4. Docker support can be deferred if needed
5. Maintain backward compatibility with existing features
6. Use feature flags for gradual rollout
7. Consider A/B testing for UI changes
8. Document all security decisions
9. Create runbooks for common issues
10. Plan for internationalization from the start
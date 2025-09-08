# MCP Config Manager

A cross-platform GUI utility for managing Model Context Protocol (MCP) server configurations across Claude, Gemini, and other AI systems.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## 🚀 Features

### Current Features
- ✅ JSON configuration file parsing and validation
- ✅ Basic server management (add, remove, edit)
- ✅ Import/export configurations
- ✅ Cross-platform Python implementation

### Planned Features
- [ ] **User-Friendly GUI** - Intuitive graphical interface with drag-and-drop management
- [ ] **Multi-Client Compatibility** - Support for `.claude.json`, `.gemini/settings.json`, and other formats
- [ ] **Quick Enable/Disable** - Toggle servers on/off without deleting configurations
- [ ] **Status/Health Monitoring** - Real-time server connection status and error reporting
- [ ] **Project-Specific Profiles** - Different configurations for different projects/agents
- [ ] **Secure Credential Handling** - Integration with system keyring for API keys
- [ ] **Audit Log/Change History** - Track all configuration changes over time
- [ ] **Advanced JSON Editor** - Both GUI and raw JSON editing capabilities

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### From Source (Development)
```bash
git clone https://github.com/yourusername/mcp-config-manager.git
cd mcp-config-manager
pip install -r requirements.txt
python -m src.mcp_config_manager
🖼️ Screenshots
Screenshots will be added as the GUI is developed
🛠️ Development
This project is in early development. We welcome contributions! See CONTRIBUTING.md for development setup and guidelines.
Quick Start for Developers
bash# Clone the repository
git clone https://github.com/yourusername/mcp-config-manager.git
cd mcp-config-manager

# Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# Run tests
pytest

# Run the application
python -m src.mcp_config_manager
🗺️ Development Roadmap
Phase 1: Foundation (Current)

 Project structure and documentation
 Basic Python script functionality
 Core configuration parsing library
 Basic CLI interface
 Comprehensive testing suite

Phase 2: GUI Development

 GUI framework selection and setup
 Basic server management interface
 Import/export functionality
 Cross-platform packaging

Phase 3: Advanced Features

 Health monitoring and status checking
 Profile and project management
 Security and credential management
 Advanced editing capabilities

Phase 4: Polish & Distribution

 Installer packages for all platforms
 Auto-updater functionality
 Comprehensive user documentation
 Community tutorials and guides

🤝 Contributing
We welcome contributions from developers of all skill levels! Here are some ways you can help:

🐛 Report bugs by creating issues
💡 Suggest features for the roadmap
📝 Improve documentation
🔧 Submit code via pull requests
🧪 Write tests to improve coverage
🎨 Design UI/UX mockups

See our Contributing Guidelines for more details.
📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
🙏 Acknowledgments

The Anthropic team for developing the Model Context Protocol
The open source community for inspiration and support
All contributors who help make this project better

📞 Support

🐛 Bug Reports: GitHub Issues
💬 Discussions: GitHub Discussions
📧 Email: [your-email@example.com]


Note: This project is in active development. Features and APIs may change as we work toward a stable release.

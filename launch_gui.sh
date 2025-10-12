#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m mcp_config_manager.cli gui

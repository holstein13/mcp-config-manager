"""
Command Line Interface for MCP Config Manager
Enhanced with interactive functionality from mcp_toggle.py
"""

import click
import json
from pathlib import Path
from typing import Dict, Any

from . import __version__
from .core.config_manager import ConfigManager


def print_status(config_manager: ConfigManager, mode: str):
    """Print current server status"""
    active, disabled = config_manager.list_servers(mode)
    
    print("\n📊 Current Status:")
    print("-" * 30)
    
    mode_display = {
        'both': '🔄 Both CLIs (synced)',
        'claude': '📘 Claude only',
        'gemini': '💎 Gemini only'
    }
    print(f"Mode: {mode_display.get(mode, mode)}")
    
    if active:
        print("\n✅ ACTIVE servers (will run):")
        for i, server in enumerate(active, 1):
            print(f"  [{i}] {server}")
    else:
        print("\n✅ ACTIVE servers: None")
    
    if disabled:
        print("\n❌ DISABLED servers (won't run):")
        for i, server in enumerate(disabled, 1):
            print(f"  [d{i}] {server}")
    else:
        print("\n❌ DISABLED servers: None")


def interactive_mode():
    """Run the interactive MCP server manager"""
    print("\n🔧 MCP Config Manager - Interactive Mode")
    print("=" * 50)
    
    config_manager = ConfigManager()
    
    # Select CLI mode
    print("\n🎯 Select CLI mode:")
    print("  [1] Claude only")
    print("  [2] Gemini only") 
    print("  [3] Both (sync servers)")
    
    mode_choice = input("Mode (default=3): ").strip() or '3'
    
    if mode_choice == '1':
        mode = 'claude'
        print("📘 Managing Claude CLI only")
    elif mode_choice == '2':
        mode = 'gemini'
        print("💎 Managing Gemini CLI only")
    else:
        mode = 'both'
        print("🔄 Managing both Claude & Gemini (synced)")
    
    # Create backups
    backups = config_manager.create_backups()
    for name, path in backups:
        print(f"✅ {name} backup: {path}")
    
    # Sync if in both mode
    if mode == 'both':
        claude_data, gemini_data = config_manager.load_configs()
        claude_data, gemini_data = config_manager.sync_configurations(claude_data, gemini_data)
        config_manager.save_configs(claude_data, gemini_data, mode)
    
    while True:
        print_status(config_manager, mode)
        
        print("\n📋 Actions:")
        print("  [1-N]  Disable active server")
        print("  [d1-N] Enable disabled server")
        print("  [a]    Enable ALL")
        print("  [n]    Disable ALL")
        print("  [m]    Minimal (context7 + browsermcp)")
        print("  [w]    Web dev (+ playwright)")
        print("  [+]    ➕ Add new MCP server")
        print("  [p]    📁 Preset management")
        print("  [c]    🔄 Change CLI mode")
        print("  [s]    Save and exit")
        print("  [q]    Quit without saving")
        
        choice = input("\nAction: ").lower().strip()
        
        if choice == 'q':
            print("❌ Exiting without saving")
            break
            
        elif choice == 's':
            print("\n⚠️  Restart Claude/Gemini CLI for changes to take effect")
            break
            
        elif choice == 'c':
            # Change CLI mode
            print("\n🎯 Select new CLI mode:")
            print("  [1] Claude only")
            print("  [2] Gemini only")
            print("  [3] Both (sync servers)")
            
            new_mode = input("Mode: ").strip()
            if new_mode == '1':
                mode = 'claude'
                print("📘 Switched to Claude only")
            elif new_mode == '2':
                mode = 'gemini'
                print("💎 Switched to Gemini only")
            else:
                mode = 'both'
                claude_data, gemini_data = config_manager.load_configs()
                claude_data, gemini_data = config_manager.sync_configurations(claude_data, gemini_data)
                config_manager.save_configs(claude_data, gemini_data, mode)
                print("🔄 Switched to both (synced)")
            
        elif choice == 'a':
            count = config_manager.enable_all_servers(mode)
            print(f"✅ Enabled {count} servers")
                
        elif choice == 'n':
            count = config_manager.disable_all_servers(mode)
            print(f"❌ Disabled {count} servers")
                
        elif choice == 'm':
            active_servers = config_manager.apply_preset_mode('minimal', mode)
            print(f"✅ Minimal mode: {', '.join(active_servers)}")
            
        elif choice == 'w':
            active_servers = config_manager.apply_preset_mode('webdev', mode)
            print(f"✅ Web dev mode: {', '.join(active_servers)}")
            
        elif choice == '+':
            add_new_server_interactive(config_manager, mode)
            
        elif choice == 'p':
            preset_management_interactive(config_manager, mode)
            
        elif choice.startswith('d'):
            # Enable disabled server
            try:
                idx = int(choice[1:]) - 1
                active, disabled = config_manager.list_servers(mode)
                if 0 <= idx < len(disabled):
                    success = config_manager.enable_server(disabled[idx], mode)
                    if success:
                        print(f"✅ Enabled: {disabled[idx]}")
                    else:
                        print(f"❌ Failed to enable: {disabled[idx]}")
                else:
                    print("❌ Invalid server number")
            except ValueError:
                print("❌ Invalid input")
                
        else:
            # Disable active server
            try:
                idx = int(choice) - 1
                active, disabled = config_manager.list_servers(mode)
                if 0 <= idx < len(active):
                    success = config_manager.disable_server(active[idx], mode)
                    if success:
                        print(f"❌ Disabled: {active[idx]}")
                    else:
                        print(f"❌ Failed to disable: {active[idx]}")
                else:
                    print("❌ Invalid server number")
            except ValueError:
                print("❌ Invalid input")


def add_new_server_interactive(config_manager: ConfigManager, mode: str):
    """Interactive new server addition"""
    print("\n" + "="*60)
    print("➕ ADD NEW MCP SERVER")
    print("="*60)
    print("\nPaste the JSON configuration for your new MCP server.")
    print("Example:")
    print('''
"servername": {
  "command": "npx",
  "args": ["-y", "@package/name@latest"]
}
''')
    print("Paste your JSON below (press Enter twice when done):")
    print("-"*40)
    
    json_lines = []
    while True:
        line = input()
        if line == "" and json_lines and json_lines[-1] == "":
            break
        json_lines.append(line)
    
    if json_lines and json_lines[-1] == "":
        json_lines.pop()
    
    json_text = "\n".join(json_lines).strip()
    
    if not json_text:
        print("❌ No JSON provided")
        return
    
    # Try to determine if we need a server name
    try:
        parsed = json.loads(json_text)
        if isinstance(parsed, dict) and ('command' in parsed or 'args' in parsed):
            # Single server config, need name
            server_name = input("\nServer name: ").strip()
            if not server_name:
                print("❌ Server name required")
                return
            
            success, message = config_manager.add_server_from_json(json_text, server_name, mode)
        else:
            # Multiple servers or already has name
            success, message = config_manager.add_server_from_json(json_text, None, mode)
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")


def preset_management_interactive(config_manager: ConfigManager, mode: str):
    """Interactive preset management"""
    while True:
        presets = config_manager.list_presets()
        
        print("\n📁 PRESET MANAGEMENT")
        print("="*30)
        
        if presets:
            print("\n📋 Available presets:")
            for i, preset_name in enumerate(presets, 1):
                print(f"  [{i}] {preset_name}")
        else:
            print("\n📋 No presets available")
        
        print("\n🔧 Actions:")
        print("  [1-N]  Load preset")
        print("  [s]    Save current as new preset")
        print("  [b]    Back to main menu")
        
        choice = input("\nPreset action: ").strip()
        
        if choice == 'b':
            break
        elif choice == 's':
            preset_name = input("Preset name: ").strip()
            if not preset_name:
                print("❌ Preset name required")
                continue
            
            description = input("Description: ").strip() or "No description"
            
            try:
                config_manager.save_current_as_preset(preset_name, description, mode)
                print(f"✅ Saved preset: {preset_name}")
            except Exception as e:
                print(f"❌ Failed to save preset: {e}")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(presets):
                    preset_name = presets[idx]
                    success = config_manager.load_preset(preset_name, mode)
                    if success:
                        print(f"✅ Loaded preset: {preset_name}")
                    else:
                        print(f"❌ Failed to load preset: {preset_name}")
                else:
                    print("❌ Invalid preset number")
            except ValueError:
                print("❌ Invalid input")


@click.group()
@click.version_option(version=__version__)
def cli():
    """MCP Config Manager - Manage your MCP server configurations"""
    pass


@cli.command()
def interactive():
    """Launch interactive server management mode"""
    interactive_mode()


@cli.command()
def gui():
    """Launch the GUI interface"""
    from .gui.main_window import run_gui_in_main_thread
    run_gui_in_main_thread()



@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
def validate(config_file):
    """Validate an MCP configuration file"""
    click.echo(f"Validating {config_file}...")
    
    config_manager = ConfigManager()
    
    try:
        if 'claude' in str(config_file).lower():
            claude_data = config_manager.claude_parser.parse(Path(config_file))
            valid = config_manager.claude_parser.validate(claude_data)
        elif 'gemini' in str(config_file).lower():
            gemini_data = config_manager.gemini_parser.parse(Path(config_file))
            valid = config_manager.gemini_parser.validate(gemini_data)
        else:
            # Try both parsers
            try:
                claude_data = config_manager.claude_parser.parse(Path(config_file))
                valid = config_manager.claude_parser.validate(claude_data)
            except:
                gemini_data = config_manager.gemini_parser.parse(Path(config_file))
                valid = config_manager.gemini_parser.validate(gemini_data)
        
        if valid:
            click.echo("✅ Configuration is valid")
        else:
            click.echo("❌ Configuration has errors")
            
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")


@cli.command()
@click.option('--mode', type=click.Choice(['claude', 'gemini', 'both']), default='both')
def status(mode):
    """Show current server status"""
    config_manager = ConfigManager()
    print_status(config_manager, mode)


@cli.command()
@click.argument('server_name')
@click.option('--mode', type=click.Choice(['claude', 'gemini', 'both']), default='both')
def enable(server_name, mode):
    """Enable a specific server"""
    config_manager = ConfigManager()
    success = config_manager.enable_server(server_name, mode)
    
    if success:
        click.echo(f"✅ Enabled: {server_name}")
    else:
        click.echo(f"❌ Failed to enable: {server_name}")


@cli.command()
@click.argument('server_name')
@click.option('--mode', type=click.Choice(['claude', 'gemini', 'both']), default='both')
def disable(server_name, mode):
    """Disable a specific server"""
    config_manager = ConfigManager()
    success = config_manager.disable_server(server_name, mode)
    
    if success:
        click.echo(f"❌ Disabled: {server_name}")
    else:
        click.echo(f"❌ Failed to disable: {server_name}")


@cli.command()
@click.option('--mode', type=click.Choice(['claude', 'gemini', 'both']), default='both')
def disable_all(mode):
    """Disable all servers"""
    config_manager = ConfigManager()
    count = config_manager.disable_all_servers(mode)
    click.echo(f"❌ Disabled {count} servers")


@cli.command()
@click.option('--mode', type=click.Choice(['claude', 'gemini', 'both']), default='both')
def enable_all(mode):
    """Enable all servers"""
    config_manager = ConfigManager()
    count = config_manager.enable_all_servers(mode)
    click.echo(f"✅ Enabled {count} servers")


@cli.command()
@click.argument('preset_mode', type=click.Choice(['minimal', 'webdev', 'fullstack', 'testing']))
@click.option('--mode', type=click.Choice(['claude', 'gemini', 'both']), default='both')
def preset(preset_mode, mode):
    """Apply a preset configuration"""
    config_manager = ConfigManager()
    active_servers = config_manager.apply_preset_mode(preset_mode, mode)
    click.echo(f"✅ Applied {preset_mode} preset: {', '.join(active_servers)}")


@cli.command()
@click.option('--project-id', help='Google Cloud Project ID (default: from env or config)')
def google_auth(project_id):
    """Authenticate with Google for Gemini Code Assist"""
    import os

    config_manager = ConfigManager()

    # Set project ID if provided
    if project_id:
        result = config_manager.set_google_cloud_project(project_id)
        if result['success']:
            click.echo(f"✅ {result['message']}")
        else:
            click.echo(f"❌ {result['error']}")
            return

    # Get project ID (from arg, config, or env)
    current_project_id = config_manager.get_google_cloud_project()

    if not current_project_id:
        click.echo("❌ Google Cloud Project ID not configured")
        click.echo("\nPlease set your project ID using one of these methods:")
        click.echo("1. Use --project-id flag: mcp-config-manager google-auth --project-id YOUR_PROJECT_ID")
        click.echo("2. Set environment variable: export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID")
        click.echo("3. Use set-google-project command: mcp-config-manager set-google-project YOUR_PROJECT_ID")
        return

    click.echo(f"🔐 Using Google Cloud Project: {current_project_id}")

    # Check if already authenticated
    if config_manager.is_google_authenticated():
        click.echo("✅ Already authenticated with Google")
        if click.confirm("Do you want to re-authenticate?"):
            config_manager.clear_google_credentials()
        else:
            return

    # Get OAuth client ID
    click.echo("\n📋 OAuth Client Setup")
    click.echo("You need an OAuth 2.0 Client ID from Google Cloud Console.")
    click.echo("Visit: https://console.cloud.google.com/apis/credentials")
    click.echo("")

    client_id = click.prompt("OAuth Client ID")
    client_secret = click.prompt("OAuth Client Secret (optional, press Enter to skip)", default="", hide_input=True, show_default=False)

    if not client_secret:
        client_secret = None

    click.echo("\n🔄 Starting authentication flow...")
    result = config_manager.authenticate_google(client_id, client_secret)

    if result['success']:
        click.echo(f"✅ {result['message']}")
        click.echo("\nYou can now use Gemini Code Assist with your Google account!")
    else:
        click.echo(f"❌ {result['error']}")
        click.echo("\nTroubleshooting:")
        click.echo("1. Ensure your browser can reach localhost:8080")
        click.echo("2. Check that the Gemini for Cloud API is enabled in your project")
        click.echo("3. Verify you have the necessary permissions")


@cli.command()
@click.argument('project_id')
def set_google_project(project_id):
    """Set the Google Cloud Project ID for Gemini"""
    config_manager = ConfigManager()
    result = config_manager.set_google_cloud_project(project_id)

    if result['success']:
        click.echo(f"✅ {result['message']}")

        # Also set environment variable for current session
        import os
        os.environ['GOOGLE_CLOUD_PROJECT'] = project_id

        click.echo(f"\n💡 To make this permanent, add to your shell config:")
        click.echo(f'   echo \'export GOOGLE_CLOUD_PROJECT="{project_id}"\' >> ~/.bashrc')
        click.echo(f"   source ~/.bashrc")
    else:
        click.echo(f"❌ {result['error']}")


@cli.command()
def google_status():
    """Check Google authentication status"""
    config_manager = ConfigManager()

    # Check project ID
    project_id = config_manager.get_google_cloud_project()
    if project_id:
        click.echo(f"📁 Google Cloud Project: {project_id}")
    else:
        click.echo("❌ Google Cloud Project: Not configured")

    # Check authentication
    if config_manager.is_google_authenticated():
        click.echo("✅ Google Authentication: Valid")

        creds = config_manager.get_google_credentials()
        if creds:
            if 'expires_at' in creds:
                click.echo(f"⏰ Token expires: {creds['expires_at']}")
    else:
        click.echo("❌ Google Authentication: Not authenticated")

    click.echo("\n💡 Use 'mcp-config-manager google-auth' to authenticate")


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()

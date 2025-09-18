"""
Google OAuth authentication for Gemini Code Assist
Handles OAuth flow and credential caching for Google Cloud Project
"""

import os
import json
import webbrowser
import secrets
from pathlib import Path
from typing import Dict, Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
import base64
import hashlib
import requests


class GoogleAuthManager:
    """Manages Google OAuth authentication for Gemini Code Assist"""

    OAUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    REDIRECT_PORT = 8080
    REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

    SCOPES = [
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/generative-language.retriever"
    ]

    def __init__(self, project_id: Optional[str] = None):
        """Initialize Google Auth Manager

        Args:
            project_id: Google Cloud Project ID (can be overridden by env var)
        """
        self.project_id = project_id or os.environ.get('GOOGLE_CLOUD_PROJECT')
        self.config_dir = Path.home() / '.mcp_config_manager' / 'auth'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_path = self.config_dir / 'google_credentials.json'
        self.auth_code = None
        self.auth_error = None

    def is_authenticated(self) -> bool:
        """Check if valid credentials exist"""
        if not self.credentials_path.exists():
            return False

        try:
            with open(self.credentials_path, 'r') as f:
                creds = json.load(f)

            if 'access_token' not in creds:
                return False

            # Check if token is expired
            if 'expires_at' in creds:
                import datetime
                expiry = datetime.datetime.fromisoformat(creds['expires_at'])
                if datetime.datetime.now() >= expiry:
                    # Try to refresh if we have refresh token
                    if 'refresh_token' in creds:
                        return self._refresh_token(creds)
                    return False

            return True

        except (json.JSONDecodeError, KeyError):
            return False

    def get_credentials(self) -> Optional[Dict[str, str]]:
        """Get cached credentials if available"""
        if not self.is_authenticated():
            return None

        with open(self.credentials_path, 'r') as f:
            return json.load(f)

    def authenticate(self, client_id: str, client_secret: Optional[str] = None) -> Tuple[bool, str]:
        """Perform OAuth authentication flow

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret (optional for installed app flow)

        Returns:
            Tuple of (success, message)
        """
        if not self.project_id:
            return False, "GOOGLE_CLOUD_PROJECT environment variable not set"

        # Generate PKCE challenge for security
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')

        # Build authorization URL
        auth_params = {
            'client_id': client_id,
            'redirect_uri': self.REDIRECT_URI,
            'response_type': 'code',
            'scope': ' '.join(self.SCOPES),
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'access_type': 'offline',
            'prompt': 'consent'
        }

        auth_url = f"{self.OAUTH_ENDPOINT}?" + '&'.join(
            f"{k}={v}" for k, v in auth_params.items()
        )

        # Start local server to receive callback
        server_thread = threading.Thread(
            target=self._run_callback_server,
            daemon=True
        )
        server_thread.start()

        # Open browser for authentication
        print(f"\nOpening browser for Google authentication...")
        print(f"If browser doesn't open, visit: {auth_url}\n")
        webbrowser.open(auth_url)

        # Wait for callback (timeout after 2 minutes)
        timeout = 120
        start_time = time.time()

        while self.auth_code is None and self.auth_error is None:
            if time.time() - start_time > timeout:
                return False, "Authentication timeout - no response received"
            time.sleep(0.5)

        if self.auth_error:
            return False, f"Authentication failed: {self.auth_error}"

        # Exchange authorization code for tokens
        token_params = {
            'client_id': client_id,
            'code': self.auth_code,
            'code_verifier': code_verifier,
            'grant_type': 'authorization_code',
            'redirect_uri': self.REDIRECT_URI
        }

        if client_secret:
            token_params['client_secret'] = client_secret

        try:
            response = requests.post(self.TOKEN_ENDPOINT, data=token_params)
            response.raise_for_status()

            tokens = response.json()

            # Add expiry timestamp
            if 'expires_in' in tokens:
                import datetime
                expires_at = datetime.datetime.now() + datetime.timedelta(
                    seconds=tokens['expires_in']
                )
                tokens['expires_at'] = expires_at.isoformat()

            # Add project ID
            tokens['project_id'] = self.project_id

            # Save credentials
            with open(self.credentials_path, 'w') as f:
                json.dump(tokens, f, indent=2)

            return True, "Authentication successful! Credentials cached."

        except requests.exceptions.RequestException as e:
            return False, f"Failed to exchange code for tokens: {str(e)}"

    def _refresh_token(self, creds: Dict) -> bool:
        """Refresh access token using refresh token"""
        if 'refresh_token' not in creds:
            return False

        refresh_params = {
            'refresh_token': creds['refresh_token'],
            'grant_type': 'refresh_token'
        }

        # Add client_id if present
        if 'client_id' in creds:
            refresh_params['client_id'] = creds['client_id']

        try:
            response = requests.post(self.TOKEN_ENDPOINT, data=refresh_params)
            response.raise_for_status()

            new_tokens = response.json()

            # Update credentials
            creds['access_token'] = new_tokens['access_token']
            if 'expires_in' in new_tokens:
                import datetime
                expires_at = datetime.datetime.now() + datetime.timedelta(
                    seconds=new_tokens['expires_in']
                )
                creds['expires_at'] = expires_at.isoformat()

            # Save updated credentials
            with open(self.credentials_path, 'w') as f:
                json.dump(creds, f, indent=2)

            return True

        except requests.exceptions.RequestException:
            return False

    def _run_callback_server(self):
        """Run local HTTP server to receive OAuth callback"""

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(handler_self):
                # Parse callback URL
                parsed = urlparse(handler_self.path)

                if parsed.path == '/callback':
                    params = parse_qs(parsed.query)

                    if 'code' in params:
                        self.auth_code = params['code'][0]
                        handler_self.send_response(200)
                        handler_self.send_header('Content-Type', 'text/html')
                        handler_self.end_headers()
                        handler_self.wfile.write(b"""
                            <html><body>
                            <h1>Authentication Successful!</h1>
                            <p>You can close this window and return to the application.</p>
                            </body></html>
                        """)
                    elif 'error' in params:
                        self.auth_error = params.get('error_description', ['Unknown error'])[0]
                        handler_self.send_response(400)
                        handler_self.send_header('Content-Type', 'text/html')
                        handler_self.end_headers()
                        handler_self.wfile.write(b"""
                            <html><body>
                            <h1>Authentication Failed</h1>
                            <p>Please return to the application and try again.</p>
                            </body></html>
                        """)
                else:
                    handler_self.send_response(404)
                    handler_self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress server logs

        server = HTTPServer(('localhost', self.REDIRECT_PORT), CallbackHandler)
        server.timeout = 120
        server.handle_request()

    def clear_credentials(self):
        """Clear cached credentials"""
        if self.credentials_path.exists():
            self.credentials_path.unlink()

    def set_project_id(self, project_id: str):
        """Update Google Cloud Project ID"""
        self.project_id = project_id

        # Update cached credentials if they exist
        if self.credentials_path.exists():
            try:
                with open(self.credentials_path, 'r') as f:
                    creds = json.load(f)

                creds['project_id'] = project_id

                with open(self.credentials_path, 'w') as f:
                    json.dump(creds, f, indent=2)
            except (json.JSONDecodeError, KeyError):
                pass
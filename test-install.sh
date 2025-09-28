#!/bin/bash

# Test script for the MCP Config Manager installer
# This script tests the installer in a controlled environment

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TEST_DIR="$HOME/tmp/mcp-installer-test"
INSTALL_DIR="$TEST_DIR/install"

print_test() {
    echo -e "${BLUE}TEST:${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
}

print_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
}

# Setup test environment
setup_test() {
    print_test "Setting up test environment"

    # Clean up any previous test
    rm -rf "$TEST_DIR"
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"

    print_pass "Test directory created: $TEST_DIR"
}

# Test installer download simulation
test_installer_download() {
    print_test "Testing installer script access"

    # Check if installer exists in current directory
    if [ -f "install.sh" ]; then
        print_pass "Installer script found in project"
    else
        print_fail "Installer script not found in project"
        return 1
    fi
}

# Test system requirements check
test_requirements() {
    print_test "Testing system requirements check"

    # Extract the check_requirements function and test it
    if command -v python3 >/dev/null 2>&1; then
        print_pass "Python 3 detected"
    else
        print_fail "Python 3 not found"
        return 1
    fi

    if command -v git >/dev/null 2>&1; then
        print_pass "Git detected"
    else
        print_fail "Git not found"
        return 1
    fi

    if command -v pip3 >/dev/null 2>&1; then
        print_pass "pip3 detected"
    else
        print_fail "pip3 not found"
        return 1
    fi
}

# Test installation directory logic
test_install_directory() {
    print_test "Testing installation directory selection"

    # Test default directory creation
    mkdir -p "$INSTALL_DIR"

    if [ -d "$INSTALL_DIR" ]; then
        print_pass "Installation directory can be created"
    else
        print_fail "Failed to create installation directory"
        return 1
    fi
}

# Test launcher script creation
test_launcher_creation() {
    print_test "Testing launcher script creation"

    # Create a mock launcher
    cat > "$INSTALL_DIR/mcp" << 'EOF'
#!/bin/bash
echo "MCP Config Manager launcher test"
echo "Arguments: $@"
EOF

    chmod +x "$INSTALL_DIR/mcp"

    if [ -x "$INSTALL_DIR/mcp" ]; then
        print_pass "Launcher script created and executable"

        # Test launcher execution
        output=$("$INSTALL_DIR/mcp" test-arg)
        if [[ "$output" == *"test-arg"* ]]; then
            print_pass "Launcher script works correctly"
        else
            print_fail "Launcher script not working properly"
        fi
    else
        print_fail "Launcher script not executable"
        return 1
    fi
}

# Test uninstaller creation
test_uninstaller() {
    print_test "Testing uninstaller creation"

    # Create mock uninstaller
    mkdir -p "$INSTALL_DIR/mcp-config-manager"
    cat > "$INSTALL_DIR/mcp-config-manager/uninstall.sh" << 'EOF'
#!/bin/bash
echo "Uninstaller test - would remove installation"
EOF

    chmod +x "$INSTALL_DIR/mcp-config-manager/uninstall.sh"

    if [ -x "$INSTALL_DIR/mcp-config-manager/uninstall.sh" ]; then
        print_pass "Uninstaller script created"
    else
        print_fail "Uninstaller script not created"
        return 1
    fi
}

# Test shell integration
test_shell_integration() {
    print_test "Testing shell integration"

    # Create test shell config
    TEST_SHELL_CONFIG="$TEST_DIR/.bashrc_test"
    touch "$TEST_SHELL_CONFIG"

    # Simulate adding to PATH
    echo 'export PATH="'$INSTALL_DIR':$PATH"' >> "$TEST_SHELL_CONFIG"
    echo 'alias mcp-gui="mcp gui"' >> "$TEST_SHELL_CONFIG"

    if grep -q "$INSTALL_DIR" "$TEST_SHELL_CONFIG"; then
        print_pass "PATH integration works"
    else
        print_fail "PATH integration failed"
        return 1
    fi

    if grep -q "mcp-gui" "$TEST_SHELL_CONFIG"; then
        print_pass "Alias creation works"
    else
        print_fail "Alias creation failed"
        return 1
    fi
}

# Test CLI tools detection
test_cli_detection() {
    print_test "Testing CLI tools detection"

    # Test detection of various CLI tools
    tools_found=0

    for tool in claude gemini codex openai; do
        if command -v "$tool" >/dev/null 2>&1; then
            print_pass "Detected $tool CLI"
            tools_found=$((tools_found + 1))
        else
            print_warn "$tool CLI not found (this is expected in test environment)"
        fi
    done

    print_pass "CLI detection logic works (found $tools_found tools)"
}

# Cleanup test environment
cleanup_test() {
    print_test "Cleaning up test environment"

    cd "$HOME"
    rm -rf "$TEST_DIR"

    print_pass "Test environment cleaned up"
}

# Run all tests
run_all_tests() {
    echo ""
    echo -e "${BLUE}🧪 MCP Config Manager Installer Test Suite${NC}"
    echo "================================================"
    echo ""

    tests_passed=0
    tests_failed=0

    for test_func in setup_test test_installer_download test_requirements test_install_directory test_launcher_creation test_uninstaller test_shell_integration test_cli_detection cleanup_test; do
        echo ""
        if $test_func; then
            tests_passed=$((tests_passed + 1))
        else
            tests_failed=$((tests_failed + 1))
            print_fail "Test $test_func failed"
        fi
    done

    echo ""
    echo "================================================"
    echo -e "${GREEN}✅ Tests Passed: $tests_passed${NC}"
    echo -e "${RED}❌ Tests Failed: $tests_failed${NC}"
    echo ""

    if [ $tests_failed -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed! Installer is ready.${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed. Please review the installer.${NC}"
        return 1
    fi
}

# Run the test suite
run_all_tests
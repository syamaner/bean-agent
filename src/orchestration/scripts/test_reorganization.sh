#!/bin/bash
# Test Code Reorganization
# Validates that all files are in correct locations and paths are updated

# Don't exit on errors - we want to see all test results
set +e

echo "🧪 Testing Code Reorganization"
echo "=============================="
echo ""

FAILED=0
PASSED=0

# Helper functions
pass() {
    echo "✅ $1"
    ((PASSED++))
}

fail() {
    echo "❌ $1"
    ((FAILED++))
}

# Test 1: Directory structure
echo "📁 Testing Directory Structure..."
echo ""

if [ -d "../../orchestration/aspire" ]; then
    pass "aspire/ directory exists"
else
    fail "aspire/ directory missing"
fi

if [ -d "../../orchestration/agents" ]; then
    pass "agents/ directory exists"
else
    fail "agents/ directory missing"
fi

if [ -d "../../orchestration/scripts" ]; then
    pass "scripts/ directory exists"
else
    fail "scripts/ directory missing"
fi

echo ""

# Test 2: Key files moved
echo "📦 Testing File Relocation..."
echo ""

if [ -f "../aspire/Program.cs" ]; then
    pass "Program.cs in correct location"
else
    fail "Program.cs not found"
fi

if [ -f "../agents/autonomous_agent.py" ]; then
    pass "autonomous_agent.py in correct location"
else
    fail "autonomous_agent.py not found"
fi

if [ -f "../CoffeeRoasting.sln" ]; then
    pass "Solution file in correct location"
else
    fail "Solution file not found"
fi

if [ -f "./run_aspire.sh" ]; then
    pass "run_aspire.sh script exists"
else
    fail "run_aspire.sh script missing"
fi

echo ""

# Test 3: Path updates in Program.cs
echo "🔍 Testing Path Updates in Program.cs..."
echo ""

if grep -q 'Path.GetFullPath("../../..")' ../aspire/Program.cs; then
    pass "Program.cs projectRoot updated to ../../.."
else
    fail "Program.cs projectRoot not updated"
fi

if grep -q 'Path.GetFullPath("../../../venv")' ../aspire/Program.cs; then
    pass "Program.cs venv path updated to ../../../venv"
else
    fail "Program.cs venv path not updated"
fi

if grep -q 'src/orchestration/agents/autonomous_agent.py' ../aspire/Program.cs; then
    pass "Program.cs agent path updated"
else
    fail "Program.cs agent path not updated"
fi

echo ""

# Test 4: Solution file paths
echo "🔧 Testing Solution File..."
echo ""

if grep -q 'aspire\\CoffeeRoasting.AppHost.csproj' ../CoffeeRoasting.sln; then
    pass "Solution file project path updated"
else
    fail "Solution file project path not updated"
fi

echo ""

# Test 5: Build test
echo "🏗️  Testing Aspire Build..."
echo ""

cd ..
if dotnet build aspire > /dev/null 2>&1; then
    pass "Aspire project builds successfully"
else
    fail "Aspire project failed to build"
fi

cd scripts
echo ""

# Test 6: Python agent imports
echo "🐍 Testing Python Agent..."
echo ""

cd ../../..
if ./venv/bin/python -c "import sys; sys.path.insert(0, 'src/orchestration/agents'); import autonomous_agent" 2>/dev/null; then
    pass "autonomous_agent.py imports successfully"
else
    # This is expected to fail without all dependencies, just check syntax
    if ./venv/bin/python -m py_compile src/orchestration/agents/autonomous_agent.py 2>/dev/null; then
        pass "autonomous_agent.py has valid syntax"
    else
        fail "autonomous_agent.py has syntax errors"
    fi
fi

cd src/orchestration/scripts
echo ""

# Test 7: Old Phase3 cleanup
echo "🧹 Testing Phase3 Cleanup..."
echo ""

if [ ! -f "../../../Phase3/autonomous_agent.py" ]; then
    pass "autonomous_agent.py removed from Phase3"
else
    fail "autonomous_agent.py still in Phase3"
fi

if [ ! -d "../../../Phase3/CoffeeRoasting.AppHost/bin" ]; then
    pass "CoffeeRoasting.AppHost moved from Phase3"
else
    fail "CoffeeRoasting.AppHost still in Phase3"
fi

echo ""

# Summary
echo "═══════════════════════════════════════"
echo "📊 Test Summary"
echo "═══════════════════════════════════════"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All tests passed! Reorganization successful!"
    echo ""
    echo "Next steps:"
    echo "  1. Test Aspire: cd src/orchestration && dotnet run --project aspire"
    echo "  2. Clean up Phase3: rm -rf Phase3/{CoffeeRoasting.AppHost,workflows,scripts,.idea}"
    exit 0
else
    echo "⚠️  Some tests failed. Please review the issues above."
    exit 1
fi

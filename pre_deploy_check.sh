#!/bin/bash

# Pre-Deployment Verification Script
# Run this before deploying to Render

echo "🔍 AI Financial Advisor - Pre-Deployment Check"
echo "================================================"
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

echo "📁 Checking File Structure..."
echo "--------------------------------"

# Check backend files
if [ -f "backend/main.py" ]; then
    check_pass "backend/main.py exists"
else
    check_fail "backend/main.py missing"
fi

if [ -f "backend/requirements.txt" ]; then
    check_pass "backend/requirements.txt exists"
else
    check_fail "backend/requirements.txt missing"
fi

# Check frontend files
if [ -f "frontend/package.json" ]; then
    check_pass "frontend/package.json exists"
else
    check_fail "frontend/package.json missing"
fi

if [ -f "frontend/vite.config.ts" ]; then
    check_pass "frontend/vite.config.ts exists"
else
    check_fail "frontend/vite.config.ts missing"
fi

# Check configuration files
if [ -f "render.yaml" ]; then
    check_pass "render.yaml exists"
else
    check_warn "render.yaml missing (optional but recommended)"
fi

if [ -f ".gitignore" ]; then
    check_pass ".gitignore exists"
else
    check_warn ".gitignore missing"
fi

echo ""
echo "🔐 Checking Sensitive Files..."
echo "--------------------------------"

# Check for .env files (should NOT be in git)
if [ -f "backend/.env" ]; then
    if grep -q "backend/.env" .gitignore 2>/dev/null; then
        check_pass "backend/.env in .gitignore"
    else
        check_fail "backend/.env exists but NOT in .gitignore!"
    fi
fi

if [ -f "frontend/.env" ]; then
    if grep -q "frontend/.env" .gitignore 2>/dev/null; then
        check_pass "frontend/.env in .gitignore"
    else
        check_fail "frontend/.env exists but NOT in .gitignore!"
    fi
fi

echo ""
echo "📦 Checking Dependencies..."
echo "--------------------------------"

# Check Python dependencies
if [ -f "backend/requirements.txt" ]; then
    if grep -q "fastapi" backend/requirements.txt; then
        check_pass "FastAPI in requirements.txt"
    else
        check_fail "FastAPI missing from requirements.txt"
    fi
    
    if grep -q "uvicorn" backend/requirements.txt; then
        check_pass "Uvicorn in requirements.txt"
    else
        check_fail "Uvicorn missing from requirements.txt"
    fi
    
    if grep -q "sqlalchemy" backend/requirements.txt; then
        check_pass "SQLAlchemy in requirements.txt"
    else
        check_fail "SQLAlchemy missing from requirements.txt"
    fi
    
    if grep -q "pgvector" backend/requirements.txt; then
        check_pass "pgvector in requirements.txt"
    else
        check_fail "pgvector missing from requirements.txt"
    fi
    
    if grep -q "openai" backend/requirements.txt; then
        check_pass "OpenAI in requirements.txt"
    else
        check_fail "OpenAI missing from requirements.txt"
    fi
fi

# Check Node dependencies
if [ -f "frontend/package.json" ]; then
    if grep -q '"build"' frontend/package.json; then
        check_pass "Build script in package.json"
    else
        check_fail "Build script missing from package.json"
    fi
fi

echo ""
echo "🔧 Checking Configuration..."
echo "--------------------------------"

# Check if git is initialized
if [ -d ".git" ]; then
    check_pass "Git repository initialized"
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        check_warn "Uncommitted changes detected"
    else
        check_pass "No uncommitted changes"
    fi
    
    # Check if remote is set
    if git remote -v | grep -q "origin"; then
        check_pass "Git remote 'origin' configured"
        REMOTE_URL=$(git remote get-url origin 2>/dev/null)
        echo "   Remote: $REMOTE_URL"
    else
        check_warn "No git remote configured"
    fi
else
    check_warn "Not a git repository"
fi

echo ""
echo "📋 Environment Variables Checklist..."
echo "--------------------------------"
echo ""
echo "You will need these environment variables on Render:"
echo ""
echo "Required:"
echo "  - SECRET_KEY (generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\")"
echo "  - GOOGLE_CLIENT_ID"
echo "  - GOOGLE_CLIENT_SECRET"
echo "  - HUBSPOT_CLIENT_ID"
echo "  - HUBSPOT_CLIENT_SECRET"
echo "  - OPENAI_API_KEY"
echo "  - FRONTEND_URL (add after deploying frontend)"
echo "  - CORS_ORIGINS (add after deploying frontend)"
echo "  - DATABASE_URL (auto-added by Render)"
echo ""
echo "Optional:"
echo "  - OPENAI_API_BASE"
echo "  - GOOGLE_PROJECT_ID"
echo ""

echo ""
echo "================================"
echo "📊 Summary"
echo "================================"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "You're ready to deploy to Render!"
    echo ""
    echo "Next steps:"
    echo "1. Commit and push to GitHub"
    echo "2. Follow RENDER_DEPLOYMENT_GUIDE.md"
    echo "3. Use DEPLOYMENT_CHECKLIST.md as you go"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo ""
    echo "You can proceed with deployment, but review the warnings above."
    echo ""
    echo "Next steps:"
    echo "1. Review warnings (optional)"
    echo "2. Commit and push to GitHub"
    echo "3. Follow RENDER_DEPLOYMENT_GUIDE.md"
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    fi
    echo ""
    echo "Please fix the errors above before deploying."
    exit 1
fi


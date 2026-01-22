#!/bin/bash

# Quick GitHub Setup Script
# This script will initialize git and show you the commands to create the repo

set -e

echo "🚀 Setting up distributed-compute-locally for GitHub..."
echo ""

# Initialize git
echo "📦 Initializing Git repository..."
git init

# Add all files
echo "📝 Adding files..."
git add .

# Show what will be committed
echo ""
echo "Files to be committed:"
git diff --cached --stat
echo ""

# Commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: Distributed compute library with beautiful CLI

Features:
- Distribute workloads across multiple devices
- Beautiful CLI with ASCII logo
- Load balancing and fault tolerance
- pip installable package
- Comprehensive documentation and tests"

echo ""
echo "✅ Git repository initialized!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📤 NEXT STEPS: Create GitHub Repository"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Option 1: Using GitHub CLI (easiest)"
echo "  gh auth login"
echo "  gh repo create distributed-compute-locally --public --source=. --remote=origin --push"
echo ""
echo "Option 2: Manual setup"
echo "  1. Go to: https://github.com/new"
echo "  2. Repository name: distributed-compute-locally"
echo "  3. Make it PUBLIC"
echo "  4. Do NOT initialize with README"
echo "  5. Click 'Create repository'"
echo ""
echo "  Then run these commands (replace YOUR-USERNAME):"
echo "  git remote add origin https://github.com/YOUR-USERNAME/distributed-compute-locally.git"
echo "  git branch -M main"
echo "  git push -u origin main"
echo ""
echo "🎉 Your code is ready for GitHub!"
echo ""

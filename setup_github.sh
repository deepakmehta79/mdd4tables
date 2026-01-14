#!/bin/bash
# Script to push mdd4tables to GitHub
# Run this from the mdd4tables directory

set -e

echo "=== Setting up Git repository ==="

# Initialize git if not already
if [ ! -d .git ]; then
    git init
    echo "✓ Initialized git repository"
else
    echo "✓ Git repository already exists"
fi

# Configure git (uncomment and edit if needed)
# git config user.name "Your Name"
# git config user.email "your.email@example.com"

# Stage all files
git add -A
echo "✓ Staged all files"

# Create initial commit (or commit changes)
git commit -m "Initial commit: mdd4tables library with documentation" --allow-empty 2>/dev/null || \
git commit -m "Update: mdd4tables library with documentation" 2>/dev/null || \
echo "✓ No changes to commit"

# Set main branch
git branch -M main
echo "✓ Set main branch"

# Instructions for adding remote and pushing
echo ""
echo "=== Next Steps ==="
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Name it: mdd4tables"
echo "   - Do NOT initialize with README, .gitignore, or license"
echo "   - Click 'Create repository'"
echo ""
echo "2. Add the remote and push (replace YOUR_USERNAME):"
echo "   git remote add origin https://github.com/YOUR_USERNAME/mdd4tables.git"
echo "   git push -u origin main"
echo ""
echo "3. Enable GitHub Pages:"
echo "   - Go to Settings → Pages"
echo "   - Source: GitHub Actions"
echo ""
echo "Your docs will be at: https://YOUR_USERNAME.github.io/mdd4tables/"


#!/bin/bash

# Release script for PDF AudioBook Reader
# This script helps create a new release

echo "🚀 PDF AudioBook Reader - Release Script"
echo "========================================"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes"
    echo "Please commit your changes before creating a release"
    git status --short
    exit 1
fi

# Get current version from git tags
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "📋 Current version: $CURRENT_VERSION"

# Ask for new version
echo ""
read -p "🏷️  Enter new version (e.g., v1.0.0): " NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    echo "❌ Error: Version cannot be empty"
    exit 1
fi

# Validate version format
if [[ ! $NEW_VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Version must be in format v1.0.0"
    exit 1
fi

# Ask for release notes
echo ""
read -p "📝 Enter release notes: " RELEASE_NOTES

if [ -z "$RELEASE_NOTES" ]; then
    RELEASE_NOTES="Release $NEW_VERSION"
fi

echo ""
echo "📦 Creating release $NEW_VERSION..."
echo "📝 Release notes: $RELEASE_NOTES"
echo ""

# Create and push tag
git tag -a "$NEW_VERSION" -m "$RELEASE_NOTES"
git push origin "$NEW_VERSION"

echo "✅ Release $NEW_VERSION created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Go to GitHub repository"
echo "2. Navigate to Releases"
echo "3. Create a new release from tag $NEW_VERSION"
echo "4. Add detailed release notes"
echo "5. Deploy to your chosen platform"
echo ""
echo "🌐 Deployment options:"
echo "- Render.com (recommended for free hosting)"
echo "- Railway.app"
echo "- Heroku"
echo "- Vercel"
echo ""
echo "🎉 Happy deploying!"

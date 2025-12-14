#!/usr/bin/env python3
"""
Bump version numbers across the project.

Usage:
    python scripts/bump_version.py patch   # 1.0.0 -> 1.0.1
    python scripts/bump_version.py minor   # 1.0.0 -> 1.1.0
    python scripts/bump_version.py major   # 1.0.0 -> 2.0.0
    python scripts/bump_version.py beta    # 1.0.0 -> 1.0.1-beta
    python scripts/bump_version.py stable  # 1.0.1-beta -> 1.0.1
"""

import re
import sys
from pathlib import Path
from datetime import date


def get_current_version():
    """Read current version from prospect/__init__.py."""
    init_file = Path("prospect/__init__.py")
    content = init_file.read_text()

    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    raise ValueError("Could not find __version__ in prospect/__init__.py")


def parse_version(version_str):
    """Parse version string into components."""
    # Handle beta/alpha suffixes
    base_version = version_str.split("-")[0]
    parts = base_version.split(".")

    return {
        "major": int(parts[0]),
        "minor": int(parts[1]),
        "patch": int(parts[2]) if len(parts) > 2 else 0,
        "suffix": version_str.split("-")[1] if "-" in version_str else None,
    }


def bump_version(current, bump_type):
    """Calculate new version based on bump type."""
    v = parse_version(current)

    if bump_type == "major":
        return f"{v['major'] + 1}.0.0"
    elif bump_type == "minor":
        return f"{v['major']}.{v['minor'] + 1}.0"
    elif bump_type == "patch":
        return f"{v['major']}.{v['minor']}.{v['patch'] + 1}"
    elif bump_type == "beta":
        new_patch = f"{v['major']}.{v['minor']}.{v['patch'] + 1}"
        return f"{new_patch}-beta"
    elif bump_type == "stable":
        # Remove suffix
        return f"{v['major']}.{v['minor']}.{v['patch']}"
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")


def update_file(filepath, pattern, replacement):
    """Update version in a file."""
    path = Path(filepath)
    if not path.exists():
        print(f"  Skipping {filepath} (not found)")
        return False

    content = path.read_text()
    new_content = re.sub(pattern, replacement, content)

    if content != new_content:
        path.write_text(new_content)
        print(f"  Updated {filepath}")
        return True
    else:
        print(f"  No changes in {filepath}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/bump_version.py [major|minor|patch|beta|stable]")
        sys.exit(1)

    bump_type = sys.argv[1].lower()

    if bump_type not in ["major", "minor", "patch", "beta", "stable"]:
        print(f"Unknown bump type: {bump_type}")
        print("Valid options: major, minor, patch, beta, stable")
        sys.exit(1)

    current = get_current_version()
    new_version = bump_version(current, bump_type)

    print(f"\nBumping version: {current} -> {new_version}\n")

    # Update prospect/__init__.py
    update_file(
        "prospect/__init__.py",
        r'__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{new_version}"',
    )

    # Update VERSION_INFO in __init__.py
    v = parse_version(new_version)
    update_file("prospect/__init__.py", r'"major":\s*\d+', f'"major": {v["major"]}')
    update_file("prospect/__init__.py", r'"minor":\s*\d+', f'"minor": {v["minor"]}')
    update_file("prospect/__init__.py", r'"patch":\s*\d+', f'"patch": {v["patch"]}')

    release_type = "beta" if v.get("suffix") == "beta" else "stable"
    update_file(
        "prospect/__init__.py", r'"release":\s*"[^"]+"', f'"release": "{release_type}"'
    )

    # Update pyproject.toml
    update_file("pyproject.toml", r'version\s*=\s*"[^"]+"', f'version = "{new_version}"')

    print(f"\nVersion bumped to {new_version}")
    print(f"\nNext steps:")
    print(f"  1. Update CHANGELOG.md with changes")
    print(f"  2. git add -A")
    print(f"  3. git commit -m 'chore: bump version to {new_version}'")
    print(f"  4. git tag v{new_version}")
    print(f"  5. git push && git push --tags")


if __name__ == "__main__":
    main()

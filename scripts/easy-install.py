#!/usr/bin/env python3
"""
easy-install.py

Convenience installer to:
- Check for required commands (python3, pip, git)
- On Debian/Ubuntu: install common system packages (via apt)
- On macOS/Homebrew: install common system packages (via brew)
- Install pipx and then install the bench CLI (frappe-bench) in a safe per-user way

Usage:
  sudo python3 scripts/easy-install.py    # to allow system package installation (apt/brew)
  python3 scripts/easy-install.py --no-system  # skip system package manager steps

This script tries to be conservative: it asks before running package manager installs.
"""
import argparse
import os
import shutil
import subprocess
import sys

def run(cmd, check=True, capture=False):
    print("+", " ".join(cmd))
    return subprocess.run(cmd, check=check, stdout=(subprocess.PIPE if capture else None))

def have_cmd(name):
    return shutil.which(name) is not None

def confirm(prompt):
    resp = input(prompt + " [y/N]: ").strip().lower()
    return resp == "y" or resp == "yes"

def install_on_apt():
    packages = [
        "python3-venv", "python3-dev", "python3-pip", "git", "redis-server",
        "nodejs", "npm", "yarn", "build-essential", "mariadb-server", "libmariadb-dev-compat", "libmariadb-dev"
    ]
    print("Will attempt to install system packages via apt:", " ".join(packages))
    if not confirm("Proceed with apt install (requires sudo)?"):
        print("Skipping apt installation.")
        return
    run(["sudo", "apt", "update"])
    run(["sudo", "apt", "install", "-y"] + packages)

def install_on_brew():
    packages = ["python", "git", "redis", "node", "yarn", "mariadb"]
    print("Will attempt to install system packages via brew:", " ".join(packages))
    if not confirm("Proceed with brew install?"):
        print("Skipping brew installation.")
        return
    run(["brew", "update"])
    run(["brew", "install"] + packages)

def ensure_pipx():
    if have_cmd("pipx"):
        print("pipx already installed.")
        return
    print("pipx not found, installing via pip (user).")
    run([sys.executable, "-m", "pip", "install", "--user", "pipx"])
    # Try to add to PATH via ensurepath if available
    try:
        run([sys.executable, "-m", "pipx", "ensurepath"])
    except Exception:
        pass
    print("If pipx is not available in your PATH, restart your shell to pick up ~/.local/bin or equivalent.")

def install_bench_with_pipx():
    # frappe-bench is the modern package name for bench CLI
    print("Installing bench CLI (frappe-bench) via pipx.")
    run([sys.executable, "-m", "pipx", "install", "frappe-bench"], check=False)
    print("bench CLI should now be available as 'bench' in your PATH (you may need to restart your shell).")

def main():
    parser = argparse.ArgumentParser(description="Easy install helper for bench / frappe environment")
    parser.add_argument("--no-system", action="store_true", help="Skip system package manager installs")
    args = parser.parse_args()

    print("Checking essential tools...")
    missing = []
    for c in ("python3", "git"):
        if not have_cmd(c):
            missing.append(c)
    if missing:
        print("Missing required commands:", ", ".join(missing))
    else:
        print("Found python3 and git.")

    # System package installation (best-effort)
    if not args.no_system:
        if have_cmd("apt"):
            install_on_apt()
        elif have_cmd("brew"):
            install_on_brew()
        else:
            print("No supported system package manager detected (apt or brew). Skipping system package installation.")
    else:
        print("--no-system specified, skipping system package installs.")

    # Ensure pipx and bench
    try:
        ensure_pipx()
    except Exception as e:
        print("Warning: pipx installation failed or was skipped:", e)

    try:
        install_bench_with_pipx()
    except Exception as e:
        print("Failed to install bench via pipx. You can try: pipx install frappe-bench")
        print("Error:", e)

    print("\nDone. Next steps (example):")
    print("  1) Restart your shell to ensure pipx binaries are on PATH (if needed).")
    print("  2) From the repo root run: bash scripts/setup_bench.sh")
    print("See docs/bench-setup.md for full instructions.")

if __name__ == "__main__":
    main()
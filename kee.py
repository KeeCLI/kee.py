#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kee — AWS CLI profile manager
A simple tool to manage multiple AWS accounts with SSO and easy account switching.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict
import configparser

BOLD_WHITE = "\033[1;37m"
RESET = "\033[0m"


def get_kee_art():
    """Return the Kee ASCII art banner."""
    return """
    ██╗  ██╗███████╗███████╗
    ██║ ██╔╝██╔════╝██╔════╝
    █████╔╝ █████╗  █████╗
    ██╔═██╗ ██╔══╝  ██╔══╝
    ██║  ██╗███████╗███████╗
    ╚═╝  ╚═╝╚══════╝╚══════╝

    AWS CLI profile manager"""


def hlt(text):
    return f"{BOLD_WHITE}{text}{RESET}"


class KeeConfig:
    """Manages configuration storage."""

    def __init__(self):
        self.config_dir = Path.home() / ".aws"
        self.config_file = self.config_dir / "kee.json"
        self.config_dir.mkdir(exist_ok=True)

    def load_config(self) -> Dict:
        """Load configuration."""
        if not self.config_file.exists():
            return {"accounts": {}, "current_account": None}

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"accounts": {}, "current_account": None}

    def save_config(self, config: Dict):
        """Save configuration."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)


class AWSConfigManager:
    """Manages AWS CLI configuration files."""

    def __init__(self):
        self.aws_config_file = Path.home() / ".aws" / "config"

    def _write_config_with_formatting(self, config: configparser.ConfigParser):
        """Write config file with proper formatting and cross-platform compatibility."""
        with open(self.aws_config_file, "w", encoding="utf-8", newline="\n") as f:
            for section_name in config.sections():
                f.write(f"[{section_name}]\n")
                for key, value in config.items(section_name):
                    f.write(f"{key} = {value}\n")
                f.write("\n")  # Add empty line after each section

    def remove_profile(self, profile_name: str):
        """Remove a profile from AWS config."""
        if not self.aws_config_file.exists():
            return

        config = configparser.ConfigParser()
        config.read(self.aws_config_file, encoding="utf-8")

        section_name = (
            f"profile {profile_name}" if profile_name != "default" else "default"
        )

        if config.has_section(section_name):
            config.remove_section(section_name)
            self._write_config_with_formatting(config)

    def reformat_config_file(self):
        """Reformat the entire AWS config file with proper spacing."""
        if not self.aws_config_file.exists():
            return

        config = configparser.ConfigParser()
        config.read(self.aws_config_file, encoding="utf-8")
        self._write_config_with_formatting(config)


class KeeManager:
    """Main kee profile manager."""

    def __init__(self):
        self.config = KeeConfig()
        self.aws_config = AWSConfigManager()

    def add_account(self, account_name: str) -> bool:
        """Add a new AWS account with interactive configuration."""
        profile_name = account_name

        print("\n Starting SSO configuration...")
        print(" (This will open your browser to complete authentication.)")
        print("\n Follow the prompts:")
        print(f"  {hlt('1.')} Enter your SSO start URL")
        print(f"  {hlt('2.')} Enter your SSO region")
        print(f"  {hlt('3.')} Authenticate in your browser")
        print(f"  {hlt('4.')} Select your AWS account")
        print(f"  {hlt('5.')} Select your role")
        print(f"  {hlt('7.')} Choose your output format (recommend: json)")
        print(
            f"\n  {hlt('Tip:')} A session can be liked to multiple profiles.\n  When prompted for a 'session name', use something generic, like your company name.\n"
        )

        try:
            result = subprocess.run(
                ["aws", "configure", "sso", "--profile", profile_name],
                timeout=300,
                check=False,
            )

            if result.returncode != 0:
                print(" [X] SSO configuration failed.")
                return False

            print(
                f"\n {hlt('Note:')} You can ignore the AWS CLI example above.\n {hlt('Kee')} will handle profiles for you."
            )

            # Reformat the AWS config file to add proper spacing
            self.aws_config.reformat_config_file()

            # Read the created profile to get the details
            profile_info = self._read_profile_info(profile_name)
            if not profile_info:
                print(" [X] Could not read profile information.")
                return False

            # Save to kee config
            config_data = self.config.load_config()
            config_data["accounts"][account_name] = {
                "profile_name": profile_name,
                "sso_start_url": profile_info.get("sso_start_url", ""),
                "sso_region": profile_info.get("sso_region", ""),
                "sso_account_id": profile_info.get("sso_account_id", "unknown"),
                "sso_role_name": profile_info.get("sso_role_name", "unknown"),
                "session_name": profile_info.get("session_name", ""),
            }
            self.config.save_config(config_data)

            # Test the profile
            if self._check_credentials(profile_name):
                print("\n [✓] The profile was added and it's working!")
            else:
                print(
                    "\n [X] I created the profile but credentials may need a refresh..."
                )
                print(f" {hlt('Try:')} aws sso login --profile {profile_name}")

            return True

        except subprocess.TimeoutExpired:
            print(" [X] The SSO configuration timed out.")
            return False
        except Exception as e:
            print(f" [X] I got an error while adding the account: {hlt(e)}")
            return False

    def _read_profile_info(self, profile_name: str) -> Dict:
        """Read profile information from AWS config."""
        try:
            config = configparser.ConfigParser()
            config.read(self.aws_config.aws_config_file, encoding="utf-8")

            section_name = f"profile {profile_name}"
            if not config.has_section(section_name):
                return {}

            profile_info = dict(config.items(section_name))

            # Handle SSO session format
            if "sso_session" in profile_info:
                session_name = profile_info["sso_session"]
                profile_info["session_name"] = session_name

                # Get SSO details from the sso-session section
                sso_section_name = f"sso-session {session_name}"
                if config.has_section(sso_section_name):
                    sso_info = dict(config.items(sso_section_name))
                    profile_info["sso_start_url"] = sso_info.get("sso_start_url", "")
                    profile_info["sso_region"] = sso_info.get("sso_region", "")
            else:
                # Legacy format - SSO details in profile section
                profile_info["session_name"] = profile_info.get("sso_session", "")

            # Ensure required fields have defaults
            profile_info.setdefault("sso_start_url", "")
            profile_info.setdefault("sso_region", "")
            profile_info.setdefault("sso_account_id", "unknown")
            profile_info.setdefault("sso_role_name", "unknown")

            return profile_info

        except Exception as e:
            print(f" [X] Error reading profile info: {hlt(e)}")
            return {}

    def list_accounts(self):
        """List all configured accounts."""
        config_data = self.config.load_config()
        accounts = config_data.get("accounts", {})
        current_account = config_data.get("current_account")

        if not accounts:
            print(
                f"\n No accounts configured.\n Use '{hlt('kee add <account_name>')}' to add an account."
            )
            return

        print()
        for account_name, account_info in accounts.items():
            status = " (Current profile)" if account_name == current_account else ""
            print(f" {hlt(account_name)}{status}")

            # Show account info
            account_id = account_info["sso_account_id"]
            role = account_info["sso_role_name"]

            print(f" • {hlt('Account:')} {account_id}")
            print(f" • {hlt('Role:')} {role}")

    def remove_account(self, account_name: str) -> bool:
        """Remove an account configuration."""
        config_data = self.config.load_config()
        accounts = config_data.get("accounts", {})

        if account_name not in accounts:
            print(f"\n Account '{hlt(account_name)}' not found.")
            return False

        # Confirm removal
        confirm = input(
            f"\n Are you sure you want to remove account '{hlt(account_name)}'? (y/N): "
        )
        if confirm.lower() != "y":
            return False

        # Remove from kee config
        account_info = accounts[account_name]
        profile_name = account_info["profile_name"]
        del accounts[account_name]

        # Clear current account if it's the one being removed
        if config_data.get("current_account") == account_name:
            config_data["current_account"] = None

        self.config.save_config(config_data)

        # Remove the AWS profile from config file
        hlt_account = hlt(account_name)
        try:
            self.aws_config.remove_profile(profile_name)
            print(f" [✓] Profile '{hlt_account}' has been removed.")

        except Exception as e:
            print(f" [✓] Profile '{hlt_account}' removed from {hlt('Kee')}.")
            print(
                f" [!] {hlt('Warning:')} Could not remove AWS profile '{hlt(profile_name)}': {e}"
            )
            print(" You may want to remove it manually from ~/.aws/config")

        return True

    def use_account(self, account_name: str) -> bool:
        """Use an account and start a sub-shell."""
        # Check if we're already using a Kee profile
        if os.environ.get("KEE_ACTIVE_PROFILE"):
            current_profile = os.environ.get("KEE_CURRENT_ACCOUNT", "unknown")
            print(f"\n You are using a {hlt('Kee')} profile: {hlt(current_profile)}")
            print(f" Exit the current session first by typing '{hlt('exit')}'")
            return False

        config_data = self.config.load_config()
        accounts = config_data.get("accounts", {})
        hlt_account = hlt(account_name)

        if account_name not in accounts:
            print(f"\n Account '{hlt_account}' not found.")

            if accounts:
                print(" Available accounts:")
                for name in accounts.keys():
                    print(f" • {hlt(name)}\n")

            # Offer to add the account
            add_account = input(
                f" Would you like to add account '{hlt_account}' now? (y/N): "
            )
            if add_account.lower() == "y":
                if self.add_account(account_name):
                    # Ask if they want to use it now
                    use_now = input(
                        f" Would you like to use account '{hlt_account}' now? (y/N): "
                    )
                    if use_now.lower() == "y":
                        # Reload config to get the newly added account
                        config_data = self.config.load_config()
                        accounts = config_data.get("accounts", {})
                    else:
                        command = f"kee use {account_name}"
                        print(
                            f"\n Account '{hlt_account}' is ready to use. Run '{hlt(command)}' when needed."
                        )
                        return True
                else:
                    print(f" Failed to add account '{hlt_account}'.")
                    return False
            else:
                return False

        account_info = accounts[account_name]
        profile_name = account_info["profile_name"]

        # Check and refresh SSO credentials if needed
        if not self._check_credentials(profile_name):
            print("\n Credentials expired or not available. Attempting SSO login...")
            if not self._sso_login(profile_name):
                print(
                    f" Failed to authenticate. Please run '{hlt('aws sso login')}' manually."
                )
                return False

        # Update current account
        config_data["current_account"] = account_name
        self.config.save_config(config_data)

        # Start sub-shell with AWS credentials
        self._start_subshell(account_name, profile_name)

        # Clear current account when sub-shell exits
        config_data["current_account"] = None
        self.config.save_config(config_data)

        return True

    def current_account(self):
        """Show current active account."""
        # Check if we're in a Kee profile
        if os.environ.get("KEE_ACTIVE_PROFILE"):
            current = os.environ.get("KEE_CURRENT_ACCOUNT")
            if current:
                print(f"\n Current profile: {hlt(current)}")
                print(f" Type '{hlt('exit')}' to return to your main shell.")
            else:
                print(f"\n Active {hlt('Kee')} profile but account name not found.")
        else:
            config_data = self.config.load_config()
            current = config_data.get("current_account")

            if current:
                print(f"\n Current profile: {hlt(current)}")
            else:
                print("\n No profile is currently active.")

    def _check_credentials(self, profile_name: str) -> bool:
        """Check if AWS credentials are valid."""
        try:
            env = os.environ.copy()
            env["AWS_CLI_AUTO_PROMPT"] = "off"
            env["AWS_PAGER"] = ""

            result = subprocess.run(
                ["aws", "sts", "get-caller-identity", "--profile", profile_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
                env=env,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def _sso_login(self, profile_name: str) -> bool:
        """Perform SSO login for the profile."""
        try:
            result = subprocess.run(
                ["aws", "sso", "login", "--profile", profile_name],
                timeout=300,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def _start_subshell(self, account_name: str, profile_name: str):
        """Start a sub-shell with AWS credentials configured."""
        # Get current shell - cross-platform compatible
        if os.name == "nt":  # Windows
            current_shell = os.environ.get("COMSPEC", "cmd.exe")
        else:  # Unix-like (Linux, macOS)
            current_shell = os.environ.get("SHELL", "/bin/bash")

        # Prepare environment
        env = os.environ.copy()
        env["AWS_PROFILE"] = profile_name
        env["KEE_CURRENT_ACCOUNT"] = account_name
        env["KEE_ACTIVE_PROFILE"] = "1"

        # Update prompt for Unix-like systems only
        if os.name != "nt":
            if "PS1" in env:
                env["PS1"] = f"aws:{account_name} {env['PS1']}"
            else:
                env["PS1"] = f"aws:{account_name} $ "

        # Show the Kee banner and profile info
        print(get_kee_art())
        print(f"    Profile: {hlt(account_name)}")
        print("\n    Starting a sub-shell...")
        print(f"    Type '{hlt('exit')}' to return to your main shell.")

        try:
            subprocess.run([current_shell], env=env, check=False)
        except KeyboardInterrupt:
            pass

        print(f"\n {hlt(account_name)} — Session ended.")


def main():
    """Main entry point."""
    # Set UTF-8 encoding for Windows compatibility
    if sys.platform.startswith("win"):
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

    parser = argparse.ArgumentParser(
        description=get_kee_art(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kee add myaccount          Add a new AWS account
  kee use myaccount          Use an account (starts sub-shell)
  kee list                   List all configured accounts
  kee current                Show current active account
  kee remove myaccount       Remove an account configuration
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    subparsers.add_parser("add", help="Add a new AWS account").add_argument(
        "account_name", help="Name for the account"
    )

    # Use command
    subparsers.add_parser("use", help="Use an account").add_argument(
        "account_name", help="Account to use"
    )

    # List command
    subparsers.add_parser("list", help="List all configured accounts")

    # Current command
    subparsers.add_parser("current", help="Show current active account")

    # Remove command
    subparsers.add_parser("remove", help="Remove an account").add_argument(
        "account_name", help="Account to remove"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Only instantiate KeeManager when we actually need it
    kee = KeeManager()

    try:
        if args.command == "add":
            kee.add_account(args.account_name)
        elif args.command == "use":
            kee.use_account(args.account_name)
        elif args.command == "list":
            kee.list_accounts()
        elif args.command == "current":
            kee.current_account()
        elif args.command == "remove":
            kee.remove_account(args.account_name)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Unit tests for Kee — AWS CLI profile manager
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the modules we're testing
from kee import KeeConfig, AWSConfigManager, KeeManager, get_kee_art


class TestKeeArt(unittest.TestCase):
    """Test the ASCII art function."""

    def test_get_kee_art_returns_string(self):
        """Test that get_kee_art returns a string."""
        art = get_kee_art()
        self.assertIsInstance(art, str)
        self.assertIn("AWS CLI profile manager", art)
        self.assertTrue(len(art) > 0)


class TestKeeConfig(unittest.TestCase):
    """Test the KeeConfig class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".aws"
        self.config_file = self.config_dir / "kee.json"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("kee.Path.home")
    def test_init_creates_config_dir(self, mock_home):
        """Test that KeeConfig creates the .aws directory."""
        mock_home.return_value = Path(self.temp_dir)
        config = KeeConfig()

        self.assertTrue(self.config_dir.exists())
        self.assertEqual(config.config_file, self.config_file)

    @patch("kee.Path.home")
    def test_load_config_default_when_no_file(self, mock_home):
        """Test loading default config when file doesn't exist."""
        mock_home.return_value = Path(self.temp_dir)
        config = KeeConfig()

        result = config.load_config()
        expected = {"accounts": {}, "current_account": None}
        self.assertEqual(result, expected)

    @patch("kee.Path.home")
    def test_load_config_from_file(self, mock_home):
        """Test loading config from existing file."""
        mock_home.return_value = Path(self.temp_dir)
        config = KeeConfig()

        # Create test config
        test_config = {
            "accounts": {"test-account": {"profile_name": "test-account"}},
            "current_account": "test-account",
        }

        # Write test config
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(test_config, f)

        result = config.load_config()
        self.assertEqual(result, test_config)

    @patch("kee.Path.home")
    def test_load_config_handles_invalid_json(self, mock_home):
        """Test loading config handles invalid JSON gracefully."""
        mock_home.return_value = Path(self.temp_dir)
        config = KeeConfig()

        # Create invalid JSON file
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            f.write("invalid json content")

        result = config.load_config()
        expected = {"accounts": {}, "current_account": None}
        self.assertEqual(result, expected)

    @patch("kee.Path.home")
    def test_save_config(self, mock_home):
        """Test saving config to file."""
        mock_home.return_value = Path(self.temp_dir)
        config = KeeConfig()

        test_config = {
            "accounts": {"test-account": {"profile_name": "test-account"}},
            "current_account": "test-account",
        }

        config.save_config(test_config)

        # Verify file was created and contains correct data
        self.assertTrue(self.config_file.exists())
        with open(self.config_file, "r") as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config, test_config)


class TestAWSConfigManager(unittest.TestCase):
    """Test the AWSConfigManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.aws_config_file = Path(self.temp_dir) / ".aws" / "config"
        self.aws_config_file.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("kee.Path.home")
    def test_init(self, mock_home):
        """Test AWSConfigManager initialization."""
        mock_home.return_value = Path(self.temp_dir)
        manager = AWSConfigManager()

        expected_path = Path(self.temp_dir) / ".aws" / "config"
        self.assertEqual(manager.aws_config_file, expected_path)

    @patch("kee.Path.home")
    def test_remove_profile_nonexistent_file(self, mock_home):
        """Test removing profile when config file doesn't exist."""
        mock_home.return_value = Path(self.temp_dir)
        manager = AWSConfigManager()

        # Should not raise an exception
        manager.remove_profile("test-profile")

    @patch("kee.Path.home")
    def test_remove_profile_existing(self, mock_home):
        """Test removing an existing profile."""
        mock_home.return_value = Path(self.temp_dir)
        manager = AWSConfigManager()

        # Create test config file
        config_content = """[profile test]
sso_role_name = AdministratorAccess
sso_session = test
sso_account_id = 123456789098
output = json

[profile other-profile]
sso_role_name = AdministratorAccess
"""
        with open(self.aws_config_file, "w") as f:
            f.write(config_content)

        manager.remove_profile("test")

        # Verify profile was removed
        with open(self.aws_config_file, "r") as f:
            content = f.read()

        self.assertNotIn("profile test", content)
        self.assertIn("profile other-profile", content)

    @patch("kee.Path.home")
    def test_reformat_config_file(self, mock_home):
        """Test reformatting config file."""
        mock_home.return_value = Path(self.temp_dir)
        manager = AWSConfigManager()

        # Create test config file without proper spacing
        config_content = """[profile test]
sso_role_name = AdministratorAccess
sso_session = test
[profile other-profile]
sso_role_name = AdministratorAccess"""

        with open(self.aws_config_file, "w") as f:
            f.write(config_content)

        manager.reformat_config_file()

        # Verify proper formatting
        with open(self.aws_config_file, "r") as f:
            content = f.read()

        # Should have empty lines between sections
        lines = content.split("\n")
        profile_indices = [
            i for i, line in enumerate(lines) if line.startswith("[profile")
        ]

        # Check that there are empty lines after each profile section
        self.assertTrue(any("" in lines for _ in profile_indices))


class TestKeeManager(unittest.TestCase):
    """Test the KeeManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_init(self, mock_aws_config, mock_kee_config):
        """Test KeeManager initialization."""
        manager = KeeManager()

        mock_kee_config.assert_called_once()
        mock_aws_config.assert_called_once()
        self.assertIsNotNone(manager.config)
        self.assertIsNotNone(manager.aws_config)

    @patch("kee.subprocess.run")
    @patch("kee.KeeManager._read_profile_info")
    @patch("kee.KeeManager._check_credentials")
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_add_account_success(
        self,
        mock_aws_config,
        mock_kee_config,
        mock_check_creds,
        mock_read_profile,
        mock_subprocess,
    ):
        """Test successful account addition."""
        # Setup mocks
        mock_subprocess.return_value.returncode = 0
        mock_read_profile.return_value = {
            "sso_session": "test",
            "sso_account_id": "123456789012",
            "sso_role_name": "TestRole",
            "output": "json",
        }

        mock_check_creds.return_value = True

        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = {
            "accounts": {},
            "current_account": None,
        }
        mock_kee_config.return_value = mock_config_instance

        mock_aws_config_instance = Mock()
        mock_aws_config.return_value = mock_aws_config_instance

        manager = KeeManager()

        with patch("builtins.print") as mock_print:
            result = manager.add_account("test-account")

        self.assertTrue(result)
        mock_subprocess.assert_called_once()
        mock_read_profile.assert_called_once_with("test-account")
        mock_check_creds.assert_called_once_with("test-account")
        mock_config_instance.save_config.assert_called_once()

        # Check that success messages were printed
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Check if call has positional arguments
                print_calls.append(str(call[0][0]))

        self.assertTrue(any("[✓]" in msg for msg in print_calls))

    @patch("kee.subprocess.run")
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_add_account_sso_failure(
        self, mock_aws_config, mock_kee_config, mock_subprocess
    ):
        """Test account addition when SSO configuration fails."""
        mock_subprocess.return_value.returncode = 1

        manager = KeeManager()

        with patch("builtins.print") as mock_print:
            result = manager.add_account("test-account")

        self.assertFalse(result)

        # Check that failure message was printed
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Check if call has positional arguments
                print_calls.append(str(call[0][0]))

        self.assertTrue(any("[X]" in msg and "failed" in msg for msg in print_calls))

    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_list_accounts_empty(self, mock_aws_config, mock_kee_config):
        """Test listing accounts when none are configured."""
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = {
            "accounts": {},
            "current_account": None,
        }
        mock_kee_config.return_value = mock_config_instance

        manager = KeeManager()

        with patch("builtins.print") as mock_print:
            manager.list_accounts()

        mock_print.assert_called_with(
            "\n No accounts configured. Use '\x1b[1;37mkee add <account_name>\x1b[0m' to add an account."
        )

    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_list_accounts_with_data(self, mock_aws_config, mock_kee_config):
        """Test listing accounts with configured accounts."""
        test_accounts = {
            "test-account": {
                "sso_account_id": "123456789012",
                "sso_role_name": "TestRole",
            }
        }

        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = {
            "accounts": test_accounts,
            "current_account": "test-account",
        }
        mock_kee_config.return_value = mock_config_instance

        manager = KeeManager()

        with patch("builtins.print") as mock_print:
            manager.list_accounts()

        # Check that account information was printed
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Check if call has positional arguments
                print_calls.append(call[0][0])

        self.assertTrue(any("test-account" in str(msg) for msg in print_calls))
        self.assertTrue(any("Current profile" in str(msg) for msg in print_calls))
        self.assertTrue(any("123456789012" in str(msg) for msg in print_calls))

    @patch("builtins.input")
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_remove_account_not_found(
        self, mock_aws_config, mock_kee_config, mock_input
    ):
        """Test removing account that doesn't exist."""
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = {
            "accounts": {},
            "current_account": None,
        }
        mock_kee_config.return_value = mock_config_instance

        manager = KeeManager()

        with patch("builtins.print") as mock_print:
            result = manager.remove_account("nonexistent")

        self.assertFalse(result)
        mock_print.assert_called_with(
            "\n Account '\x1b[1;37mnonexistent\x1b[0m' not found."
        )

    @patch("builtins.input", return_value="n")
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_remove_account_cancelled(
        self, mock_aws_config, mock_kee_config, mock_input
    ):
        """Test removing account when user cancels."""
        test_accounts = {
            "test-account": {"profile_name": "test-account", "session_name": ""}
        }

        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = {
            "accounts": test_accounts,
            "current_account": None,
        }
        mock_kee_config.return_value = mock_config_instance

        manager = KeeManager()
        result = manager.remove_account("test-account")

        self.assertFalse(result)
        mock_config_instance.save_config.assert_not_called()

    @patch("builtins.input", return_value="y")
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_remove_account_success(self, mock_aws_config, mock_kee_config, mock_input):
        """Test successful account removal."""
        test_accounts = {
            "test-account": {
                "profile_name": "test-account",
                "session_name": "test-session",
            }
        }

        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = {
            "accounts": test_accounts,
            "current_account": None,
        }
        mock_kee_config.return_value = mock_config_instance

        mock_aws_config_instance = Mock()
        mock_aws_config.return_value = mock_aws_config_instance

        manager = KeeManager()

        with patch("builtins.print") as mock_print:
            result = manager.remove_account("test-account")

        self.assertTrue(result)
        mock_aws_config_instance.remove_profile.assert_called_once_with("test-account")
        mock_config_instance.save_config.assert_called_once()

        # Check success message
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Check if call has positional arguments
                print_calls.append(str(call[0][0]))

        self.assertTrue(any("[✓]" in msg and "removed" in msg for msg in print_calls))

    @patch.dict(
        os.environ, {"KEE_ACTIVE_PROFILE": "1", "KEE_CURRENT_ACCOUNT": "existing"}
    )
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_use_account_already_in_session(self, mock_aws_config, mock_kee_config):
        """Test using account when already in a session."""
        manager = KeeManager()

        with patch("builtins.print") as mock_print:
            result = manager.use_account("test-account")

        self.assertFalse(result)
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Check if call has positional arguments
                print_calls.append(str(call[0][0]))

        self.assertTrue(
            any(
                "You are using a \x1b[1;37mKee\x1b[0m profile: \x1b[1;37mexisting\x1b[0m"
                in msg
                for msg in print_calls
            )
        )

    @patch("kee.subprocess.run")
    @patch("kee.KeeManager._check_credentials")
    @patch("kee.KeeManager._sso_login")
    @patch("kee.KeeManager._start_subshell")
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_use_account_success(
        self,
        mock_aws_config,
        mock_kee_config,
        mock_subshell,
        mock_sso_login,
        mock_check_creds,
        mock_subprocess,
    ):
        """Test successful account usage."""
        test_accounts = {"test-account": {"profile_name": "test-account"}}

        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = {
            "accounts": test_accounts,
            "current_account": None,
        }
        mock_kee_config.return_value = mock_config_instance

        mock_check_creds.return_value = True

        manager = KeeManager()

        with patch.dict(os.environ, {}, clear=True):
            result = manager.use_account("test-account")

        self.assertTrue(result)
        mock_check_creds.assert_called_once_with("test-account")
        mock_subshell.assert_called_once_with("test-account", "test-account")
        mock_config_instance.save_config.assert_called()

    @patch.dict(
        os.environ, {"KEE_ACTIVE_PROFILE": "1", "KEE_CURRENT_ACCOUNT": "test-account"}
    )
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_current_account_in_session(self, mock_aws_config, mock_kee_config):
        """Test showing current account when using a profile."""
        manager = KeeManager()

        with patch("builtins.print") as mock_print:
            manager.current_account()

        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Check if call has positional arguments
                print_calls.append(str(call[0][0]))

        self.assertTrue(
            any(
                "Current profile: \x1b[1;37mtest-account\x1b[0m" in msg
                for msg in print_calls
            )
        )

    @patch("kee.subprocess.run")
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_check_credentials_success(
        self, mock_aws_config, mock_kee_config, mock_subprocess
    ):
        """Test credential checking success."""
        mock_subprocess.return_value.returncode = 0

        manager = KeeManager()
        result = manager._check_credentials("test-profile")

        self.assertTrue(result)
        mock_subprocess.assert_called_once()

    @patch("kee.subprocess.run")
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_check_credentials_failure(
        self, mock_aws_config, mock_kee_config, mock_subprocess
    ):
        """Test credential checking failure."""
        mock_subprocess.return_value.returncode = 1

        manager = KeeManager()
        result = manager._check_credentials("test-profile")

        self.assertFalse(result)

    @patch("kee.subprocess.run")
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_sso_login_success(self, mock_aws_config, mock_kee_config, mock_subprocess):
        """Test SSO login success."""
        mock_subprocess.return_value.returncode = 0

        manager = KeeManager()
        result = manager._sso_login("test-profile")

        self.assertTrue(result)

    @patch("kee.subprocess.run")
    @patch("kee.KeeConfig")
    @patch("kee.AWSConfigManager")
    def test_sso_login_failure(self, mock_aws_config, mock_kee_config, mock_subprocess):
        """Test SSO login failure."""
        mock_subprocess.return_value.returncode = 1

        manager = KeeManager()
        result = manager._sso_login("test-profile")

        self.assertFalse(result)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)

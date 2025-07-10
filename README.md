<div align="center">
  <img src="https://raw.githubusercontent.com/keecli/kee.py/refs/heads/main/kee.png" alt="Kee" />
</div>

![OSX](https://img.shields.io/badge/-OSX-black) ![OSX](https://img.shields.io/badge/-Linux-red) ![OSX](https://img.shields.io/badge/-Windows-blue)

A simple tool to manage multiple AWS accounts with SSO support and easy account access.

`Kee` creates isolated sub-shells for each AWS account, ensuring no credentials are stored locally while providing seamless account management.

> 🦀 — In case you are looking for extra speed, check out the **Rust** [implementation](https://github.com/keecli/kee.rs).<br />
> This is now the primary version — it's faster, has more features, and will receive all future updates.

## Features

- 🔐 **SSO integration**: Full support for AWS SSO authentication
- 🚀 **Easy account access**: Use any configured account with a single command
- 🐚 **Sub-shell isolation**: Each account runs in its own sub-shell with proper credential isolation
- 📝 **Custom aliases**: Use friendly names for your AWS accounts
- 🔍 **Account management**: Easily list, add, and remove accounts
- 🚫 **No stored credentials**: No AWS credentials are stored anywhere - uses AWS SSO tokens
- 🎨 **Shell integration**: Shows current account in your shell prompt
- ⚡ **Auto-refresh**: Automatically handles SSO token refresh when needed

## Security notes

- **No credential storage**: `Kee` never stores AWS access keys or secrets
- **SSO token management**: Uses AWS CLI's built-in SSO token caching
- **Sub-shell isolation**: Each profile's session is isolated in its own shell
- **Automatic cleanup**: Environment variables are cleared when exiting sub-shells

## Installation

### Prerequisites

- Python 3.7 or higher
- AWS CLI v2 installed and configured
- Access to AWS SSO

### Clone this repository:

```bash
git clone https://github.com/keecli/kee.py.git ~/.kee
```

### Option 1: Via symlink

```bash
cd ~/.kee
chmod u+x kee.py

# Create a symlink in your PATH (adjust path as needed)
sudo ln -s $(pwd)/kee.py /usr/local/bin/kee
```

### Option 2: Using pip3

```bash
cd ~/.kee
pip3 install -e .
```

## Quick Start

### 1. Add Your First Account

```bash
kee add mycompany.dev
```

This will:

- Run `aws configure sso --profile company.dev`
- Prompt you for your SSO configuration (start URL, region, etc.)
- Open your browser for SSO authentication
- Let you select your AWS account and role interactively
- Automatically save the configuration to `Kee`

> **Tip:** A session can be liked to multiple profiles. When prompted for a 'session name', use something generic, like your company name.

### 2. Use an Account

```bash
kee use mycompany.dev
```

This will:

- Check if SSO credentials are valid
- Automatically run `aws sso login` if needed
- Start a sub-shell with AWS credentials configured
- Update your shell prompt to show the active account

### 3. Work with AWS

Inside the sub-shell, all AWS CLI commands will use the selected account:

```bash
aws:mycompany.dev $ aws s3 ls
aws:mycompany.dev $ aws ec2 describe-instances
aws:mycompany.dev $ exit  # Terminate the session and return to your main shell
```

## Commands

### Add an account

```bash
kee add <account_name>
```

Interactively configure a new AWS account with SSO settings.

### Use an account

```bash
kee use <account_name>
```

Use an account and start a sub-shell with AWS credentials.

### List all accounts

```bash
kee list
```

Show all configured accounts and their details.

### Show current account

```bash
kee current
```

Display which account is currently active (if any).

### Remove an account

```bash
kee remove <account_name>
```

Removes an account configuration from `Kee` and the AWS config file.

## How It Works

### Configuration storage

- `Kee` stores its configuration in `~/.aws/kee.json`
- AWS profiles are created in `~/.aws/config` with the naming pattern using `<account_name>`
- No AWS credentials are stored - only SSO configuration

### Sub-shell environment

When you use an account, `Kee`:

1. Validates SSO credentials (refreshes if needed)
2. Updates shell prompt to show current account
3. Starts a new shell session
4. Cleans up when you exit

### Session management

`Kee` prevents you from starting a sub-shell while already in one:

```bash
aws:mycompany.dev $ kee use mycompany.prod

You are using a Kee profile: mycompany.dev
Exit the current session first by typing 'exit'
```

### Shell prompt integration

Your shell prompt will show the active account:

```bash
(mycompany.dev) user@hostname:
```

## Environment variables

When you're using a `Kee` profile, the following environment variables are set:

- `AWS_PROFILE` - The AWS profile name (e.g., `mycompany.dev`)
- `KEE_CURRENT_ACCOUNT` - The `Kee` account name (e.g., `mycompany.dev`)
- `KEE_ACTIVE_PROFILE` - Set to `1` to indicate an active `Kee` profile
- `PS1` - Updated to show the current account in your prompt (Unix-like systems only)

These variables help `Kee` manage sessions and prevent nested sub-shells.

## Configuration files

### Kee configuration (`~/.aws/kee.json`)

```json
{
  "accounts": {
    "mycompany-prod": {
      "profile_name": "mycompany.dev",
      "sso_start_url": "https://mycompany.awsapps.com/start",
      "sso_region": "ap-southeast-2",
      "sso_account_id": "123456789012",
      "sso_role_name": "AdministratorAccess",
      "session_name": "mycompany"
    }
  },
  "current_account": null
}
```

### AWS config (`~/.aws/config`)

```ini
[profile mycompany.dev]
sso_role_name = AdministratorAccess
sso_session = mycompany
sso_account_id = 123456789098
output = json

[sso-session mycompany]
sso_region = ap-southeast-2
sso_start_url = https://mycompany.awsapps.com/start
sso_registration_scopes = sso:account:access
```

## Cross-platform support

`Kee` works on:

- **macOS**: Full support with shell prompt integration
- **Linux**: Full support with shell prompt integration
- **Windows**: Full support (prompt integration not available)

## Troubleshooting

### SSO login issues

If SSO login fails:

```bash
# Manual SSO login
aws sso login --profile <account_name>

# Then try using again
kee use <account_name>
```

### Profile not found

If you get "profile not found" errors:

```bash
# Check AWS config
cat ~/.aws/config

# Re-add the account if needed
kee remove <account_name>
kee add <account_name>
```

### Permission issues

If you get permission errors:

```bash
# Check AWS credentials
aws sts get-caller-identity --profile <account_name>

# Refresh SSO login
aws sso login --profile <account_name>
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests, if applicable
5. Test your changes: `make test`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

RTFM, then RTFC... If you are still stuck or just need an additional feature, file an [issue](https://github.com/KeeCLI/kee.py/issues).

<div align="center">
✌🏼
</div>

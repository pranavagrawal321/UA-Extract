# UA-Extract

UA-Extract is a precise and fast user agent parser and device detector written in Python, built on top of the largest and most up-to-date user agent database from the [Matomo Device Detector](https://github.com/matomo-org/device-detector) project. It parses user agent strings to detect browsers, operating systems, devices (desktop, tablet, mobile, TV, cars, consoles, etc.), brands, and models, including rare and obscure ones.

UA-Extract is optimized for speed with in-memory caching and supports high-performance parsing. This project is a Python port of the [Universal Device Detection library](https://github.com/thinkwelltwd/device_detector) by [thinkwelltwd](https://github.com/thinkwelltwd), with Pythonic adaptations while maintaining compatibility with the original regex and fixture YAML files.

You can find the source code at [https://github.com/pranavagrawal321/UA-Extract](https://github.com/pranavagrawal321/UA-Extract).

## Disclaimer

This port is not an exact copy of the original code; it includes Python-specific adaptations. However, it uses the original regex and fixture YAML files to benefit from updates and pull requests to both the original and ported versions.

## Installation

Install UA-Extract using pip:

```bash
pip install ua_extract
```

### Dependencies

- **[PyYAML](https://pypi.org/project/PyYAML/)**: For parsing regex and fixture YAML files.
- **[rich](https://pypi.org/project/rich/)**: For displaying progress bars during regex and fixture updates.
- **[aiohttp](https://pypi.org/project/aiohttp/)**: For asynchronous downloads when using the GitHub API method.
- **[tenacity](https://pypi.org/project/tenacity/)**: For retry logic during API downloads.
- **[Git](https://git-scm.com/)**: Required for the `git` update method.

## Usage

### Updating Regex and Fixture Files

The regex and fixture files can become outdated and may not accurately detect newly released devices or clients. It’s recommended to update them periodically from the [Matomo Device Detector](https://github.com/matomo-org/device-detector) repository. Updates can be performed programmatically or via the command-line interface (CLI), with support for two methods: Git cloning (`git`) or GitHub API downloads (`api`).

#### Programmatic Update

Use the `Regexes` class to update regex and fixture files. Configure the update process by passing arguments to the `Regexes` constructor, then call `update_regexes()` with the desired method (`"git"` or `"api"`) and optional `dry_run` parameter. The `github_token` parameter is optional but recommended for the `api` method to avoid GitHub API rate limits (60 requests/hour unauthenticated, 5000/hour authenticated).

```python
from ua_extract import Regexes

# Update using default settings (Git method, default paths, repo, branch, etc.)
Regexes().update_regexes()

# Update using GitHub API with custom paths and a GitHub token
Regexes(
    upstream_path="/custom/regexes",
    fixtures_upstream_path="/custom/fixtures",
    client_upstream_dir="/custom/client_fixtures",
    device_upstream_dir="/custom/device_fixtures",
    repo_url="https://github.com/matomo-org/device-detector.git",
    branch="dev",
    github_token="your_token_here"
).update_regexes(method="api")

# Dry run to simulate update without modifying files
Regexes().update_regexes(method="api", dry_run=True)
```

##### `Regexes` Constructor Arguments

The `Regexes` class accepts the following arguments during initialization:

- `upstream_path` (str, default: `regexes/upstream` in the project directory): Destination path for regex files.
- `repo_url` (str, default: `"https://github.com/matomo-org/device-detector.git"`): URL of the Git repository.
- `branch` (str, default: `"master"`): Git branch to fetch (e.g., `master`, `dev`).
- `sparse_dir` (str, default: `"regexes"`): Directory in the repository for regex files.
- `sparse_fixtures_dir` (str, default: `"Tests/fixtures"`): Directory in the repository for general fixtures.
- `fixtures_upstream_path` (str, default: `tests/fixtures/upstream`): Destination path for general fixture files.
- `sparse_client_dir` (str, default: `"Tests/Parser/Client/fixtures"`): Directory in the repository for client fixtures.
- `client_upstream_dir` (str, default: `tests/parser/fixtures/upstream/client`): Destination path for client fixture files.
- `sparse_device_dir` (str, default: `"Tests/Parser/Device/fixtures"`): Directory in the repository for device fixtures.
- `device_upstream_dir` (str, default: `tests/parser/fixtures/upstream/device`): Destination path for device fixture files.
- `cleanup` (bool, default: `True`): If `True`, deletes existing files in destination paths before updating.
- `github_token` (Optional[str], default: `None`): GitHub personal access token for the API method.
- `message_callback` (Optional[callable], default: `None`): Function to handle progress messages.

##### `update_regexes` Method

The `update_regexes` method accepts the following arguments:

- `method` (str, default: `"git"`): Update method (`"git"` for cloning via Git, `"api"` for downloading via GitHub API).
- `dry_run` (bool, default: `False`): If `True`, simulates the update without modifying the filesystem.

##### Update Methods and Use Cases

- **Git Method (`method="git"`)**:
  - **Description**: Clones the repository using Git, fetching only specified directories with shallow cloning (`--depth 1`) and sparse checkout (`--filter=blob:none`).
  - **Use Case**: Ideal for users with Git installed and no API rate limit concerns.
  - **Requirements**: Requires [Git](https://git-scm.com/) installed and accessible.
  - **Process**:
    - Clones the repository into a temporary directory.
    - Sets up sparse checkout for specified directories.
    - Copies files to destination paths.
    - Creates `__init__.py` files to make destinations Python packages.
  - **Progress Feedback**: Displays a progress bar using `rich` (cloning, sparse-checkout, copying, finalizing).
  - **Error Handling**: Logs Git command failures using a message callback.
  - **Example**:
    ```python
    Regexes().update_regexes()  # Uses default settings with Git method
    ```

- **GitHub API Method (`method="api"`)**:
  - **Description**: Downloads files asynchronously from the GitHub API using `aiohttp`.
  - **Use Case**: Suitable for users without Git or with restricted Git access.
  - **Requirements**: Requires `aiohttp` and `tenacity`. A GitHub token is recommended.
  - **GitHub Token**:
    - **When Needed**: GitHub API rate limits are 60 requests/hour (unauthenticated) or 5000/hour (authenticated).
    - **How to Provide**: Pass via `github_token` in the `Regexes` constructor or `--github-token` CLI option.
    - **How to Generate**: Create a token in GitHub under Settings > Developer settings > Personal access tokens with `repo` scope.
  - **Process**:
    - Validates the repository URL format.
    - Fetches file metadata recursively.
    - Downloads files with retry logic (3 attempts, exponential backoff).
    - Saves files to destination paths.
    - Creates `__init__.py` files.
  - **Progress Feedback**: Displays a progress bar with download speed and elapsed time.
  - **Error Handling**: Logs errors (e.g., rate limits, network issues) and retries transient failures.
  - **Example**:
    ```python
    Regexes(github_token="your_token_here").update_regexes(method="api")
    ```

##### Notes for Both Methods

- **Cleanup**: If `cleanup=True`, destination directories are deleted before updating.
- **Progress**: Progress bars provide visual feedback, and messages are printed to `stderr`.
- **Temporary Directory**: The `git` method uses a temporary directory, cleaned up automatically.
- **URL Validation**: The `api` method ensures the URL matches `https://github.com/user/repo/tree/branch/path`.

#### CLI Update

Use the `ua_extract` CLI to update regex and fixture files:

```bash
ua_extract update_regexes
```

##### CLI Options

The `update_regexes` command supports the following options:

- `-p, --path` (default: `regexes/upstream`): Destination path for regex files.
- `-r, --repo` (default: `https://github.com/matomo-org/device-detector.git`): Git repository URL.
- `-b, --branch` (default: `master`): Git branch name.
- `-d, --dir` (default: `regexes`): Sparse directory for regex files.
- `--fixtures-dir` (default: `Tests/fixtures`): Sparse directory for general fixtures.
- `--fixtures-path` (default: `tests/fixtures/upstream`): Destination path for general fixtures.
- `--client-dir` (default: `Tests/Parser/Client/fixtures`): Sparse directory for client fixtures.
- `--client-path` (default: `tests/parser/fixtures/upstream/client`): Destination path for client fixtures.
- `--device-dir` (default: `Tests/Parser/Device/fixtures`): Sparse directory for device fixtures.
- `--device-path` (default: `tests/parser/fixtures/upstream/device`): Destination path for device fixtures.
- `-c, --cleanup` (default: enabled): Delete existing files before updating.
- `-m, --method` (default: `git`): Update method (`git` or `api`).
- `-g, --github-token` (default: none): GitHub personal access token for API method.
- `--dry-run` (default: disabled): Simulate update without modifying files.

##### Example Commands

```bash
# Update with default settings (Git method)
ua_extract update_regexes

# Update with custom paths and cleanup disabled
ua_extract update_regexes --path /custom/regexes --fixtures-path /custom/fixtures --client-path /custom/client --device-path /custom/device --no-cleanup

# Update using GitHub API with a token
ua_extract update_regexes --method api --github-token your_token_here

# Dry run with GitHub API
ua_extract update_regexes --method api --dry-run

# Update from a specific branch
ua_extract update_regexes --branch dev
```

##### View CLI Help

```bash
# List all commands
ua_extract help

# Detailed help for update_regexes
ua_extract help update_regexes
```

##### Notes

- The `git` method requires [Git](https://git-scm.com/) installed.
- The `api` method may hit rate limits without a token.
- Progress bars and messages provide feedback during updates.

#### Parsing User Agents

##### Full Device Detection

To get comprehensive information about a user agent:

```python
from ua_extract import DeviceDetector

ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16D57 EtsyInc/5.22 rv:52200.62.0'
device = DeviceDetector(ua).parse()

print(device.is_bot())              # >>> False
print(device.os_name())             # >>> iOS
print(device.os_version())          # >>> 12.1.4
print(device.engine())              # >>> {'default': 'WebKit'}
print(device.device_brand())        # >>> Apple
print(device.device_model())        # >>> iPhone
print(device.device_type())         # >>> smartphone
print(device.secondary_client_name())     # >>> EtsyInc
print(device.secondary_client_type())     # >>> generic
print(device.secondary_client_version())  # >>> 5.22
```

##### High-Performance Software Detection

For faster parsing, skipping bot and device hardware detection:

```python
from ua_extract import SoftwareDetector

ua = 'Mozilla/5.0 (Linux; Android 6.0; 4Good Light A103 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36'
device = SoftwareDetector(ua).parse()

print(device.client_name())         # >>> Chrome Mobile
print(device.client_type())         # >>> browser
print(device.client_version())      # >>> 58.0.3029.83
print(device.os_name())             # >>> Android
print(device.os_version())          # >>> 6.0
print(device.engine())              # >>> {'default': 'WebKit', 'versions': {28: 'Blink'}}
print(device.device_brand())        # >>> ''
print(device.device_model())        # >>> ''
print(device.device_type())         # >>> smartphone
```

##### App Information in Mobile Browser User Agents

Some mobile browser user agents include app information, as shown in the `DeviceDetector` example.

## Updating from Matomo Project

To update manually from the [Matomo Device Detector](https://github.com/matomo-org/device-detector) project:

1. Clone the Matomo repository:

   ```bash
   git clone https://github.com/matomo-org/device-detector
   ```

2. Copy the updated files to your UA-Extract project:

   ```bash
   export upstream=/path/to/cloned/matomo/device-detector
   export pdd=/path/to/python/ported/ua_extract

   cp $upstream/regexes/device/*.yml $pdd/ua_extract/regexes/upstream/device/
   cp $upstream/regexes/client/*.yml $pdd/ua_extract/regexes/upstream/client/
   cp $upstream/regexes/*.yml $pdd/ua_extract/regexes/upstream/
   cp $upstream/Tests/fixtures/* $pdd/ua_extract/tests/fixtures/upstream/
   cp $upstream/Tests/Parser/Client/fixtures/* $pdd/ua_extract/tests/parser/fixtures/upstream/client/
   cp $upstream/Tests/Parser/Device/fixtures/* $pdd/ua_extract/tests/parser/fixtures/upstream/device/
   ```

3. Review logic changes in the Matomo PHP files and update the Python code.
4. Run tests and fix any failures.

## Contributing

Contributions are welcome! Submit pull requests or issues to [https://github.com/pranavagrawal321/UA-Extract](https://github.com/pranavagrawal321/UA-Extract).

## License

This project is licensed under the MIT License, consistent with the [original Device Detector project](https://github.com/thinkwelltwd/device_detector).

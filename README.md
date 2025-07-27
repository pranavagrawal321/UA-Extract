# UA-Extract

UA-Extract is a precise and fast user agent parser and device detector written in Python, built on top of the largest and most up-to-date user agent database from the [Matomo Device Detector](https://github.com/matomo-org/device-detector) project. It parses user agent strings to detect browsers, operating systems, devices (desktop, tablet, mobile, TV, cars, consoles, etc.), brands, and models, including rare and obscure ones.

UA-Extract is optimized for speed with in-memory caching and supports high-performance parsing. This project is a Python port of the [Universal Device Detection library](https://github.com/thinkwelltwd/device_detector) by [thinkwelltwd](https://github.com/thinkwelltwd), with Pythonic adaptations while maintaining compatibility with the original regex YAML files.

You can find the source code at [https://github.com/pranavagrawal321/UA-Extract](https://github.com/pranavagrawal321/UA-Extract).

## Disclaimer

This port is not an exact copy of the original code; it includes Python-specific adaptations. However, it uses the original regex YAML files to benefit from updates and pull requests to both the original and ported versions.

## Installation

Install UA-Extract using pip:

```bash
pip install ua_extract
```

### Dependencies

- **[PyYAML](https://pypi.org/project/PyYAML/)**: For parsing regex YAML files.
- **[rich](https://pypi.org/project/rich/)**: For displaying progress bars during regex updates.
- **[aiohttp](https://pypi.org/project/aiohttp/)**: For asynchronous downloads when using the GitHub API method.
- **[tenacity](https://pypi.org/project/tenacity/)**: For retry logic during API downloads.
- **[Git](https://git-scm.com/)**: Required for the `git` update method.

## Usage

### Updating Regex Files

The regex files can become outdated and may not accurately detect newly released devices. It’s recommended to update them periodically from the [Matomo Device Detector](https://github.com/matomo-org/device-detector) repository. Updates can be performed programmatically or via the command-line interface (CLI), with support for two methods: Git cloning (`git`) or GitHub API downloads (`api`).

#### Programmatic Update

Use the `Regexes` class to update regex files. Configure the update process by passing arguments to the `Regexes` constructor, then call `update_regexes()` with the desired method (`"git"` or `"api"`). The `github_token` parameter is optional but recommended for the `api` method to avoid GitHub API rate limits (60 requests/hour unauthenticated, 5000/hour authenticated).

```python
from ua_extract import Regexes

# Update using default settings (Git method, default path, repo, branch, etc.)
Regexes().update_regexes()

# Update using GitHub API with a custom path and optional GitHub token
Regexes(upstream_path="/custom/path", repo_url="https://github.com/matomo-org/device-detector.git", branch="dev", github_token="your_token_here").update_regexes(method="api")

# Update using GitHub API without a token (may hit rate limits)
Regexes(upstream_path="/custom/path").update_regexes(method="api")
```

##### `Regexes` Constructor Arguments

The `Regexes` class accepts the following arguments during initialization:

- `upstream_path` (str, default: `regexes/upstream` in the project directory): Destination path for storing updated regex files.
- `repo_url` (str, default: `"https://github.com/matomo-org/device-detector.git"`): URL of the Git repository to fetch regex files from.
- `branch` (str, default: `"master"`): Git branch to fetch (e.g., `master`, `dev`).
- `sparse_dir` (str, default: `"regexes"`): Directory in the repository to fetch (used for sparse checkout in Git method or as the target path for API method).
- `cleanup` (bool, default: `True`): If `True`, deletes existing regex files in the destination path before updating.
- `github_token` (Optional[str], default: `None`): GitHub personal access token for the API method. Optional, but recommended to avoid rate limits (60 requests/hour unauthenticated). Provide a token to increase the limit to 5000 requests/hour.

##### `update_regexes` Method

The `update_regexes` method accepts a single argument:

- `method` (str, default: `"git"`): Update method, either `"git"` (clone via Git) or `"api"` (download via GitHub API).

##### Update Methods and Use Cases

- **Git Method (`method="git"`)**:
  - **Description**: Clones the specified repository using Git, fetching only the specified directory (e.g., `regexes`) with shallow cloning (`--depth 1`) and sparse checkout (`--filter=blob:none`) for efficiency.
  - **Use Case**: Ideal for users with Git installed and no API rate limit concerns. Suitable for large repositories or when network reliability is high.
  - **Requirements**: Requires [Git](https://git-scm.com/) to be installed and accessible in the system’s PATH.
  - **Process**:
    - Clones the repository into a temporary directory.
    - Sets up sparse checkout to fetch only the specified directory.
    - Copies the files to the destination path (`upstream_path`).
    - Creates an `__init__.py` file to make the destination a Python package.
  - **Progress Feedback**: Displays a progress bar using the `rich` library, showing stages (cloning, sparse-checkout, copying, finalizing).
  - **Error Handling**: Logs errors (e.g., Git command failures) using the `logging` module.
  - **Example**:
    ```python
    Regexes().update_regexes()  # Uses default settings with Git method
    ```

- **GitHub API Method (`method="api"`)**:
  - **Description**: Downloads files asynchronously from the GitHub API using `aiohttp`, targeting the specified repository path (e.g., `regexes`).
  - **Use Case**: Suitable for users without Git installed or when preferring HTTP-based downloads. Ideal for environments with restricted Git access.
  - **Requirements**: Requires `aiohttp` and `tenacity` packages. A GitHub personal access token is optional but recommended to avoid API rate limits.
  - **GitHub Token**:
    - **When Needed**: The GitHub API has rate limits (60 requests per hour for unauthenticated requests, 5000 for authenticated). Without a token, you may hit the rate limit, causing a `403 Forbidden` error with a message indicating the limit and reset time.
    - **How to Provide**: Pass the token via the `github_token` parameter in the `Regexes` constructor or the `--github-token` CLI option.
    - **How to Generate**: Create a token in GitHub under Settings > Developer settings > Personal access tokens with the `repo` scope.
  - **Process**:
    - Validates the repository URL format (e.g., `https://github.com/user/repo/tree/branch/path`).
    - Fetches file metadata from the GitHub API, recursively handling directories.
    - Downloads files asynchronously with retry logic (up to 3 attempts with exponential backoff) using `tenacity`.
    - Saves files to the destination path (`upstream_path`).
    - Creates an `__init__.py` file.
  - **Progress Feedback**: Displays a progress bar with download speed and elapsed time using `rich`.
  - **Error Handling**: Logs errors (e.g., rate limit exceeded, network issues) and retries transient failures.
  - **Example**:
    ```python
    Regexes(github_token="your_token_here").update_regexes(method="api")  # With token
    Regexes().update_regexes(method="api")  # Without token (may hit rate limits)
    ```

##### Notes for Both Methods

- **Cleanup**: If `cleanup=True`, the destination directory is deleted before updating to ensure a clean state.
- **Logging**: Uses the `logging` module to log progress, errors, and warnings (e.g., API rate limit issues).
- **Temporary Directory**: The `git` method uses a temporary directory for cloning, cleaned up automatically.
- **URL Validation**: The `api` method validates the GitHub URL format, ensuring it matches `https://github.com/user/repo/tree/branch/path`.

#### CLI Update

Use the `ua_extract` CLI to update regex files:

```bash
ua_extract update_regexes
```

##### CLI Options

The `update_regexes` command supports the following options, corresponding to the `Regexes` constructor arguments:

- `-p, --path` (default: `regexes/upstream` in the project directory): Destination path for regex files.
- `-r, --repo` (default: `https://github.com/matomo-org/device-detector.git`): Git repository URL.
- `-b, --branch` (default: `master`): Git branch name.
- `-d, --dir` (default: `regexes`): Sparse directory in the repository to fetch.
- `-c, --cleanup` / `--no-cleanup` (default: enabled): Delete existing regex files before updating.
- `-m, --method` (default: `git`): Update method (`git` for cloning via Git, `api` for downloading via GitHub API).
- `-g, --github-token` (default: none): GitHub personal access token for API method. Optional, but recommended to avoid rate limits (60 requests/hour unauthenticated).

##### Example Commands

```bash
# Update regex files with default settings (Git method)
ua_extract update_regexes

# Update with custom path and cleanup disabled
ua_extract update_regexes --path /custom/path --no-cleanup

# Update using GitHub API with a token
ua_extract update_regexes --method api --github-token your_token_here

# Update using GitHub API without a token (may hit rate limits)
ua_extract update_regexes --method api

# Update from a specific branch
ua_extract update_regexes --branch dev
```

##### View CLI Help

To see available commands or detailed help for a specific command:

```bash
# List all commands
ua_extract help

# Detailed help for update_regexes
ua_extract help update_regexes
```

##### Notes

- The `git` method requires [Git](https://git-scm.com/) to be installed and accessible.
- The `api` method may hit GitHub API rate limits (60 requests/hour unauthenticated). Use a GitHub personal access token to increase the limit to 5000 requests/hour.
- Progress bars provide visual feedback during updates, and errors (e.g., Git failures, API rate limits) are logged with detailed messages.

#### Parsing User Agents

##### Full Device Detection

To get comprehensive information about a user agent, including browser, OS, and device details:

```python
from ua_extract import DeviceDetector

ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16D57 EtsyInc/5.22 rv:52200.62.0'
device = DeviceDetector(ua).parse()

# Example methods
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

For faster parsing that skips bot and device hardware detection, focusing only on OS and application details:

```python
from ua_extract import SoftwareDetector

ua = 'Mozilla/5.0 (Linux; Android 6.0; 4Good Light A103 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36'
device = SoftwareDetector(ua).parse()

# Example methods
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

Some mobile browser user agents include information about the app using the browser, as shown in the `DeviceDetector` example above.

## Updating from Matomo Project

To update the regex files manually from the [Matomo Device Detector](https://github.com/matomo-org/device-detector) project:

1. Clone the Matomo repository:

   ```bash
   git clone https://github.com/matomo-org/device-detector
   ```

2. Copy the updated regex and fixture files to your UA-Extract project:

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

3. Review logic changes in the Matomo PHP files and implement corresponding updates in the Python code.
4. Run the tests and fix any that fail.

## Contributing

Contributions are welcome! Please submit pull requests or issues to [https://github.com/pranavagrawal321/UA-Extract](https://github.com/pranavagrawal321/UA-Extract).

## License

This project is licensed under the MIT License, consistent with the [original Device Detector project](https://github.com/thinkwelltwd/device_detector).

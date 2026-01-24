# UA-Extract

A Python user-agent parser and device detector powered by Matomo’s regex database — accurate, updatable, and production-ready.

[![PyPI Downloads](https://static.pepy.tech/badge/ua-extract)](https://pepy.tech/projects/ua-extract)
[![PyPI Downloads (Month)](https://static.pepy.tech/badge/ua-extract/month)](https://pepy.tech/projects/ua-extract)
[![PyPI Downloads (Week)](https://static.pepy.tech/badge/ua-extract/week)](https://pepy.tech/projects/ua-extract)

---

## Overview

**UA-Extract** is a fast and precise user-agent parser written in Python, built on top of the continuously maintained regex and fixture database from the [Matomo Device Detector](https://github.com/matomo-org/device-detector) project.

It detects:

- Browsers and applications
- Operating systems and versions
- Devices (desktop, smartphone, tablet, TV, console, car, camera, etc.)
- Brands and models
- Bots and crawlers
- Secondary clients embedded in mobile user agents

UA-Extract is optimized for performance using in-memory parsing and caching, and is designed for **long-running production services**.

This project is a Python port of the [Universal Device Detection library](https://github.com/thinkwelltwd/device_detector), adapted to Python while maintaining compatibility with Matomo’s original YAML regex and fixture files.

Source code: [https://github.com/pranavagrawal321/UA-Extract](https://github.com/pranavagrawal321/UA-Extract)

---

## Disclaimer

This is not a line-by-line port of the original PHP implementation. The parsing logic is Pythonic, but the **regex and fixture data are identical**, ensuring compatibility with upstream updates.

---

## Installation

### Stable Release (PyPI)

```bash
pip install ua_extract
```

---

### Nightly / Development Version

> 🔄 **Regex Update Frequency**: Matomo’s upstream regexes and fixtures are generally updated **daily whenever new changes are available**. The nightly / development version of UA-Extract tracks these updates closely, making it the best choice if you want the freshest device and client detection.

If you want the **latest regex updates** and any unreleased fixes or minor improvements, you can install UA-Extract directly from the GitHub repository.

This version may include:

- newer device and client regexes
- updated fixture files
- small internal changes not yet published to PyPI

> ⚠️ The nightly version is recommended for testing, experimentation, or environments that require the freshest device detection. For strict stability guarantees, prefer the PyPI release.

#### Install from GitHub

```bash
pip install git+https://github.com/pranavagrawal321/UA-Extract.git
```

#### Upgrade an existing GitHub install

```bash
pip install --upgrade git+https://github.com/pranavagrawal321/UA-Extract.git
```

---

## CLI Usage

### Install Shell Completion

```bash
ua_extract --install-completion
```

---

### Update Regex & Fixture Files

Regex and fixture files should be updated periodically to recognize newly released devices and clients.

```bash
ua_extract update_regexes
```

By default, this updates files using **Git sparse checkout** from the Matomo repository.

#### CLI Options

| Option     | Description                           |
| ---------- | ------------------------------------- |
| `--path`   | Destination directory for regex files |
| `--repo`   | Git repository URL                    |
| `--branch` | Git branch (Git method only)          |
| `--method` | Update method: `git` or `api`         |

> `--no-progress` exists for backward compatibility but has no effect and will be removed.

---

## Programmatic Updates

Regex updates can also be triggered programmatically using the `Regexes` class.

### Git Method (recommended)

Uses:

- shallow clone
- sparse checkout
- atomic backup and rollback on failure

```python
from ua_extract import Regexes

Regexes().update_regexes()
```

---

### GitHub API Method

Uses:

- asynchronous downloads (`aiohttp`)
- concurrency limiting
- exponential retry logic
- GitHub rate-limit detection

```python
from ua_extract import Regexes

Regexes(github_token="your_token").update_regexes(method="api")
```

**Notes:**

- GitHub API limits: 60 requests/hour unauthenticated, 5000/hour authenticated
- Token **does not require special scopes** (public repository access only)
- API method always pulls from the `master` branch

---

### Dry Run

```python
Regexes().update_regexes(method="api", dry_run=True)
```

---

## Update Safety Guarantees

UA-Extract ensures update safety by:

- creating backups of all destination directories
- restoring the previous state automatically on failure
- never leaving partially updated files behind

This makes it safe to run updates in CI or production environments.

---

## Parsing User Agents

### CLI Parsing

You can parse a user-agent directly from the command line using the `parse` command. The CLI outputs a JSON object containing **all detected fields**.

```bash
ua_extract parse \
  --ua "Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16D57 EtsyInc/5.22" \
  --headers '{"Accept":"*/*","X-Requested-With":"com.example.app"}'
```

#### Sample CLI JSON Output

```json
{
  "is_bot": false,
  "os_name": "iOS",
  "os_version": "12.1.4",
  "engine": {
    "default": "WebKit"
  },
  "device_brand": "Apple",
  "device_model": "iPhone",
  "device_type": "smartphone",
  "secondary_client_name": "EtsyInc",
  "secondary_client_type": "generic",
  "secondary_client_version": "5.22",
  "bot_name": null,
  "client_name": "Mobile Safari",
  "client_type": "browser",
  "client_application_id": null,
  "is_television": false,
  "uses_mobile_browser": true,
  "is_mobile": true,
  "is_desktop": false,
  "is_feature_phone": false,
  "preferred_client_name": "Mobile Safari",
  "preferred_client_version": "605.1.15",
  "preferred_client_type": "browser"
}
```

**Notes:**

- `--headers` must be a valid JSON object
- headers are optional; omit `--headers` if not needed
- the output JSON mirrors the fields shown in the Python API example below

---

### Field Reference

The following table describes every field returned by the CLI and Python API.

| Field                      | Type                | Description                                    |
| -------------------------- | ------------------- | ---------------------------------------------- |
| `is_bot`                   | bool                | Whether the user agent is identified as a bot  |
| `bot_name`                 | str \| null         | Name of the bot, if detected                   |
| `os_name`                  | str \| null         | Operating system name                          |
| `os_version`               | str \| null         | Operating system version                       |
| `engine`                   | dict \| str \| null | Rendering engine information                   |
| `device_brand`             | str \| null         | Device manufacturer                            |
| `device_model`             | str \| null         | Device model                                   |
| `device_type`              | str \| null         | Device category (smartphone, tablet, TV, etc.) |
| `client_name`              | str \| null         | Primary client (browser or app) name           |
| `client_type`              | str \| null         | Client type (browser, app, library, etc.)      |
| `client_version`           | str \| null         | Client version                                 |
| `client_application_id`    | str \| null         | Application identifier, if available           |
| `secondary_client_name`    | str \| null         | Embedded or wrapper client name                |
| `secondary_client_type`    | str \| null         | Embedded client type                           |
| `secondary_client_version` | str \| null         | Embedded client version                        |
| `is_mobile`                | bool \| null        | Whether the device is mobile                   |
| `is_desktop`               | bool \| null        | Whether the device is desktop                  |
| `is_television`            | bool \| null        | Whether the device is a TV                     |
| `uses_mobile_browser`      | bool \| null        | Whether a mobile browser is used               |
| `is_feature_phone`         | bool \| null        | Whether the device is a feature phone          |
| `preferred_client_name`    | str \| null         | Best client choice when multiple clients exist |
| `preferred_client_version` | str \| null         | Preferred client version                       |
| `preferred_client_type`    | str \| null         | Preferred client type                          |

---

### Python API

#### Full Device Detection

```python
from ua_extract import DeviceDetector

ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X)..."

headers = {
    "User-Agent": ua,
    "Accept": "*/*",
    "X-Requested-With": "com.example.app",
}

device = DeviceDetector(ua, headers=headers).parse()

# Bot & classification
device.is_bot()
device.bot_name()

# Operating system
device.os_name()
device.os_version()

# Rendering engine
device.engine()

# Device information
device.device_brand()
device.device_model()
device.device_type()

# Client (primary)
device.client_name()
device.client_type()
device.client_version()
device.client_application_id()

# Secondary client
device.secondary_client_name()
device.secondary_client_type()
device.secondary_client_version()

# Device characteristics
device.is_television()
device.uses_mobile_browser()
device.is_mobile()
device.is_desktop()
device.is_feature_phone()

# Preferred client
device.preferred_client_name()
device.preferred_client_version()
device.preferred_client_type()
```

---

#### High-Performance Software Detection

Skips hardware detection for faster parsing:

```python
from ua_extract import SoftwareDetector

device = SoftwareDetector(ua).parse()

device.client_name()
device.client_version()
device.os_name()
```

---

## Testing

```bash
python -m unittest
```

Run a single test module:

```bash
python -m ua_extract.tests.parser.test_bot
```

---

## Contributing

Contributions and bug reports are welcome: [https://github.com/pranavagrawal321/UA-Extract](https://github.com/pranavagrawal321/UA-Extract)

---

## License

MIT License — compatible with the original Device Detector project.


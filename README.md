# UA-Extract

UA-Extract is a precise and fast user agent parser and device detector written in Python, backed by the largest and most up-to-date user agent database, built on top of existing library device_detector.

UA-Extract will parse any user agent and detect the browser, operating system, device used (desktop, tablet, mobile, tv, cars, console, etc.), brand and model. DeviceDetector detects thousands of user agent strings, even from rare and obscure browsers and devices.

The UA-Extract is optimized for speed of detection, by providing optimized code and in-memory caching.

This project originated as a Python port of the Universal Device Detection library.
You can find the original code https://github.com/pranavagrawal321/UA-Extract.

## Disclaimer

This port is not an exact copy of the original code; some Pythonic adaptations were used.
However, it uses the original regex yaml files, to benefit from updates and pull request to both the original and the ported versions.

## Installation

`pip install ua_extract`

## Performance Options

[CSafeLoader](http://pyyaml.org/wiki/PyYAMLDocumentation) is used if pyyaml is configured `--with-libyaml`.

The [mrab regex](https://pypi.org/project/regex/) module is preferred if installed.

## Usage

#### The regexes can outdated and may not provide correct output for newly released devices, so it's recommended to update regexes every once in a while.

```python
from ua_extract import Regexes

Regexes().update_regexes()
```

#### This can also be done using CLI

```bash
ua_extract update_regexes
````

### Note:
This requires **[Git](https://git-scm.com/)** to be installed and accessible as in to pull the updated regexes.

#### To get all info about the useragent.

```python
from ua_extract import DeviceDetector

ua = 'Mozilla/5.0 (Linux; Android 4.3; C5502 Build/10.4.1.B.0.101)  google/1.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.136 Mobile Safari/537.36'

device = DeviceDetector(ua).parse()
print(device)
```

#### To get specific information.

```python
from ua_extract import DeviceDetector

ua = 'Mozilla/5.0 (Linux; Android 4.3; C5502 Build/10.4.1.B.0.101) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.136 Mobile Safari/537.36'

device = DeviceDetector(ua).parse()
device.is_bot()
device.os_name()
device.os_version()
device.engine()
device.device_brand_name()
device.device_brand()
device.device_model()
device.device_type()
```

#### For much faster performance, skip Bot and Device Hardware Detection and extract get OS / App details only.

```python
from ua_extract import SoftwareDetector

ua = 'Mozilla/5.0 (Linux; Android 6.0; 4Good Light A103 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36'
device = SoftwareDetector(ua).parse()

device.client_name()
device.client_short_name()
device.client_type()
device.client_version()
device.os_name()
device.os_version()
device.engine()
device.device_brand_name()
device.device_brand()
device.device_model()
device.device_type()
```

#### Many mobile browser UA strings contain the app info of the APP that's using the browser 

```python
ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16D57 EtsyInc/5.22 rv:52200.62.0'
device = DeviceDetector(ua).parse()

device.secondary_client_name()
device.secondary_client_type()
device.secondary_client_version()
```

### Updating from Matomo project

1. Clone the [Matomo](https://github.com/matomo-org/device-detector) project.
2. Iterate through the various commits and copy the fixture files with the commands below.
3. Review logic changes in the PHP files and implement them in the Python code.
4. Run the tests and fix the ones that fail.

```bash
export upstream=/path/to/cloned/matomo/device-detector
export pdd=/path/to/python/ported/device_detector

cp $upstream/regexes/device/*.yml $pdd/device_detector/regexes/upstream/device/
cp $upstream/regexes/client/*.yml $pdd/device_detector/regexes/upstream/client/
cp $upstream/regexes/*.yml $pdd/device_detector/regexes/upstream/
cp $upstream/Tests/fixtures/* $pdd/device_detector/tests/fixtures/upstream/
cp $upstream/Tests/Parser/Client/fixtures/* $pdd/device_detector/tests/parser/fixtures/upstream/client/
cp $upstream/Tests/Parser/Device/fixtures/* $pdd/device_detector/tests/parser/fixtures/upstream/device/
```

### **NOTE:**

This project is the clone of the [Device Detector](https://github.com/thinkwelltwd/device_detector) project by [thinkwelltwd](https://github.com/thinkwelltwd). The base code is same as before with some minor modifications as per requirements.
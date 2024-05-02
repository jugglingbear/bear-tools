# Lumberjack 🪓

Lumberjack is an alternative to Python's built-in `logging` package with the goal of being simpler to use while still providing useful features.

## Features ✨

- Define any number of loggers at `NOISE`, `DEBUG`, `INFO`, `WARNING`, or `ERROR` log levels
- Simultaneously send logging to:
  - Standard streams (e.g. `stdout`)
  - Files
- Globally make all loggers send logs to `list[pathlib.Path]`
- Customizeable colors for noise/debug/info/warning/error log levels 🖍️
- Banners in case user wants to make a section of logging stand out
- Register callbacks to be called when logging at specific log levels

## Examples 👨‍💻

Eager to get started? We like your style. Here are some examples

### Basic Usage 🍼

File: example1.py

```python
from bear_tools.lumberjack import Logger

def main():
    logger = Logger()  # Defaults to LogLevel.INFO

    logger.noise('blah blah blah tons of information')  # Nothing logged because log level is INFO
    logger.debug('blah blah extra information')         # Nothing logged because log level is INFO
    logger.info('Information')                          # [YYYY-mm-dd HH:MM:SS.f] [Info in example.main:9]: Information
    logger.warning('Uh oh...')                          # [YYYY-mm-dd HH:MM:SS.f] [Warning in example.main:10]: Uh oh...
    logger.error('Panic!!')                             # [YYYY-mm-dd HH:MM:SS.f] [Error in example.main:11]: Panic!!

if __name__ == '__main__':
    main()
```

### Save Logs to Files 🗄️

File: example2.py

```python
from pathlib import Path
import sys

from bear_tools.lumberjack import Logger, LogLevel

logger = Logger(
    log_level=LogLevel.DEBUG,
    output_paths=[
        Path('logs1.txt'),  # Logs saved to logs1.txt
        Path('logs2.txt'),  # Logs saved to logs2.txt
        sys.stdout          # Logs sent to stdout (optional)
    ]
)

logger.banner('Important stuff about to happen!')
logger.noise('adsfadfasfsadsdfsd')  # Does not show up in logs because log level is DEBUG
logger.debug('debug logs')
logger.info('info logs')
logger.warning('warning logs')
logger.error('error logs')
```

### Callbacks 📞

File: example3.py

```python
import sys
from bear_tools.lumberjack import Logger, LogLevel

def handle_warnings(text: str) -> None:
    print(f'😨😨😨')

def handle_errors(text: str) -> None:
    print(f"Well, that's not good... 🤮")
    sys.exit(1)

logger = Logger()
logger.register_callback(LogLevel.WARNING, handle_warnings)
logger.register_callback(LogLevel.ERROR,   handle_errors)

logger.info('Happy day, all is well')
logger.info('La la la')
logger.warning('Wait a minute...')                         # This sends logs to handle_warning
logger.error("The thing didn't do the thing we wanted!!")  # This sends logs to handle_error
logger.info('Can we recover from this?!')                  # Spoiler alert: No, we never reach this code
```

Output:

```text
[2020-04-01 19:30:00.048] [Info on line 22]: Happy day, all is well
[2020-04-01 19:30:00.049] [Info on line 23]: La la la
[2020-04-01 19:30:00.049] [Warning on line 24]: Wait a minute...
😨😨😨
[2020-04-01 19:30:00.050] [Error on line 25]: The thing didn't do the thing we wanted!!
Well, that's not good... 🤮```


# Loguring

This is the [loguru](https://github.com/Delgan/loguru/) wrapper for redirecting logging library's logs to [loguru](https://github.com/Delgan/loguru/).

## Installation
```commandline
pip install git+ssh://git@github.com/ilindrey/loguring.git
```

## Usage
Simply import `loguring` and start using it in the same way as [loguru](https://github.com/Delgan/loguru/):
```python
from loguring import logger

logger.debug("That's it, beautiful and simple logging!")
```
To disable the pre-configured sink, set the `LOGURING_AUTOINIT` variable to `False`.

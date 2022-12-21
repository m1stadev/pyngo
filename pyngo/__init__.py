from importlib.metadata import version

from ._errors import *
from .client import Client

__version__ = version(__package__)

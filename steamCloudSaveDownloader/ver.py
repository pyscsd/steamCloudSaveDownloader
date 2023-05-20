import importlib.metadata

__version__ = None

try:
    __version__ = importlib.metadata.version("scsd")
except:
    pass

if __version__ is None:
    __version__ = "Version Unknown"

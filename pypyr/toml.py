"""Toml handling."""
import tomli as toml_reader
import tomli_w as toml_writer


def read_file(path):
    """Read toml file at path and return object.

    Args:
        path (Path-like): Read file from this location.

    Returns:
        dict.
    """
    with open(path, 'rb') as file:
        return load(file)


def write_file(path, payload):
    """Write payload to path as a toml file.

    payload should not be None.

    Args:
        path (Path-like): Write file to this location.
        payload (dict-like): Serialize this object to toml string & write to
                             path.

    Returns:
        None.
    """
    with open(path, 'wb') as file:
        dump(payload, file)


def load(file):
    """Read open file object as toml.

    File-like MUST be open in binary mode.

    Args:
        file (file-like): Open file-like object.

    Returns:
        dict
    """
    return toml_reader.load(file)


def dump(payload, file):
    """Write payload to open file-like object.

    File-like MUST be open in binary mode.

    Args:
        file (file-like): Open file-like object.
        payload (dict-like): Serialize this object to toml string & write to
                             file.

    Returns:
        None.
    """
    toml_writer.dump(payload, file)

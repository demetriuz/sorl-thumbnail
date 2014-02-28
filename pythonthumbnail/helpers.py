import hashlib

# from django.core.exceptions import ImproperlyConfigured
# from django.utils.encoding import smart_text
# from django.utils.importlib import import_module
# from pythonthumbnail.helpers import import_module
import json
from pythonthumbnail.compat import encode
import sys


class ThumbnailError(Exception):
    pass


class SortedJSONEncoder(json.JSONEncoder):
    """
    A json encoder that sorts the dict keys
    """

    def __init__(self, **kwargs):
        kwargs['sort_keys'] = True
        super(SortedJSONEncoder, self).__init__(**kwargs)


def toint(number):
    """
    Helper to return rounded int for a float or just the int it self.
    """
    if isinstance(number, float):
        number = round(number, 0)
    return int(number)


def tokey(*args):
    """
    Computes a unique key from arguments given.
    """
    salt = '||'.join([str(arg) for arg in args])
    hash_ = hashlib.md5(encode(salt))
    return hash_.hexdigest()


def serialize(obj):
    return json.dumps(obj, cls=SortedJSONEncoder)


def deserialize(s):
    if isinstance(s, bytes):
        return json.loads(s.decode('utf-8'))
    return json.loads(s)


def get_module_class(class_path):
    """
    imports and returns module class from ``path.to.module.Class``
    argument
    """
    mod_name, cls_name = class_path.rsplit('.', 1)

    try:
        mod = import_module(mod_name)
    except ImportError as e:
        raise Exception('Error importing module %s: "%s"' % (mod_name, e))  #ImproperlyConfigured(('Error importing module %s: "%s"' % (mod_name, e)))

    return getattr(mod, cls_name)


# stolen from django/utils/functional.py
empty = object()


def new_method_proxy(func):
    def inner(self, *args):
        if self._wrapped is empty:
            self._setup()
        return func(self._wrapped, *args)
    return inner


class LazyObject(object):
    """
    A wrapper for another class that can be used to delay instantiation of the
    wrapped class.

    By subclassing, you have the opportunity to intercept and alter the
    instantiation. If you don't need to do that, use SimpleLazyObject.
    """
    def __init__(self):
        self._wrapped = empty

    __getattr__ = new_method_proxy(getattr)

    def __setattr__(self, name, value):
        if name == "_wrapped":
            # Assign to __dict__ to avoid infinite __setattr__ loops.
            self.__dict__["_wrapped"] = value
        else:
            if self._wrapped is empty:
                self._setup()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name):
        if name == "_wrapped":
            raise TypeError("can't delete _wrapped.")
        if self._wrapped is empty:
            self._setup()
        delattr(self._wrapped, name)

    def _setup(self):
        """
        Must be implemented by subclasses to initialise the wrapped object.
        """
        raise NotImplementedError

    # introspection support:
    __members__ = property(lambda self: self.__dir__())
    __dir__ = new_method_proxy(dir)


# stolen from django.utils.importlib
def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in range(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]




#----- LOCKS


"""
Portable file locking utilities.

Based partially on example by Jonathan Feignberg <jdf@pobox.com> in the Python
Cookbook, licensed under the Python Software License.

    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65203

Example Usage::

    >>> from django.core.files import locks
    >>> with open('./file', 'wb') as f:
    ...     locks.lock(f, locks.LOCK_EX)
    ...     f.write('Django')
"""

__all__ = ('LOCK_EX','LOCK_SH','LOCK_NB','lock','unlock')

system_type = None

try:
    import win32con
    import win32file
    import pywintypes
    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    __overlapped = pywintypes.OVERLAPPED()
    system_type = 'nt'
except (ImportError, AttributeError):
    pass

try:
    import fcntl
    LOCK_EX = fcntl.LOCK_EX
    LOCK_SH = fcntl.LOCK_SH
    LOCK_NB = fcntl.LOCK_NB
    system_type = 'posix'
except (ImportError, AttributeError):
    pass

def fd(f):
    """Get a filedescriptor from something which could be a file or an fd."""
    return hasattr(f, 'fileno') and f.fileno() or f

if system_type == 'nt':
    def lock(file, flags):
        hfile = win32file._get_osfhandle(fd(file))
        win32file.LockFileEx(hfile, flags, 0, -0x10000, __overlapped)

    def unlock(file):
        hfile = win32file._get_osfhandle(fd(file))
        win32file.UnlockFileEx(hfile, 0, -0x10000, __overlapped)
elif system_type == 'posix':
    def lock(file, flags):
        fcntl.lockf(fd(file), flags)

    def unlock(file):
        fcntl.lockf(fd(file), fcntl.LOCK_UN)
else:
    # File locking is not supported.
    LOCK_EX = LOCK_SH = LOCK_NB = None

    # Dummy functions that don't do anything.
    def lock(file, flags):
        pass

    def unlock(file):
        pass

import json
import re
from pythonthumbnail.helpers import LazyObject, empty
from pythonthumbnail.compat import urlopen, urlparse, urlsplit, \
    quote, quote_plus, \
    URLError, encode
from pythonthumbnail.helpers import ThumbnailError, \
    tokey, get_module_class, deserialize
from pythonthumbnail.parsers import parse_geometry
from pythonthumbnail.storage import Storage, ContentFile, File


def serialize_image_file(image_file):
    if image_file.size is None:
        raise ThumbnailError('Trying to serialize an ``ImageFile`` with a '
                             '``None`` size.')
    data = {
        'name': image_file.name,
        'storage': image_file.serialize_storage(),
        'size': image_file.size,
    }
    return json.dumps(data)


def deserialize_image_file(s):
    data = deserialize(s)

    class LazyStorage(LazyObject):
        def _setup(self):
            self._wrapped = get_module_class(data['storage'])()

    image_file = ImageFile(data['name'], LazyStorage())
    image_file.set_size(data['size'])
    return image_file


class BaseImageFile(object):
    def exists(self):
        raise NotImplemented()

    @property
    def width(self):
        return self.size[0]

    x = width

    @property
    def height(self):
        return self.size[1]

    y = height

    def is_portrait(self):
        return self.y > self.x

    @property
    def ratio(self):
        return float(self.x) / self.y

    @property
    def url(self):
        raise NotImplemented()


class ImageFile(BaseImageFile):
    _size = None

    def __init__(self, file_, storage=None):
        if not file_:
            raise ThumbnailError('File is empty.')

        # figure out name
        if hasattr(file_, 'name'):
            self.name = file_.name
        else:
            self.name = unicode(file_)

        # figure out storage
        if storage is not None:
            self.storage = storage
        elif hasattr(file_, 'storage'):
            self.storage = file_.storage

    def __unicode__(self):
        return self.name

    def exists(self):
        return self.storage.exists(self.name)

    def set_size(self, size=None):
        # set the size if given
        if size is not None:
            pass
        # Don't try to set the size the expensive way if it already has a
        # value.
        elif self._size is not None:
            return
        elif hasattr(self.storage, 'image_size'):
            # Storage backends can implement ``image_size`` method that
            # optimizes this.
            size = self.storage.image_size(self.name)
        self._size = list(size)

    @property
    def size(self):
        return self._size

    def read(self):
        return self.storage.open(self.name).read()

    def write(self, content):
        if not isinstance(content, File):
            content = ContentFile(content)

        self._size = None
        self.name = self.storage.save(self.name, content)
        return self.name

    def delete(self):
        return self.storage.delete(self.name)

    def serialize_storage(self):
        if isinstance(self.storage, LazyObject):
            # if storage is wrapped in a lazy object we need to get the real
            # thing.
            if self.storage._wrapped is empty:
                self.storage._setup()
            cls = self.storage._wrapped.__class__
        else:
            cls = self.storage.__class__
        return '%s.%s' % (cls.__module__, cls.__name__)

    @property
    def key(self):
        return tokey(self.name, self.serialize_storage())

    def serialize(self):
        return serialize_image_file(self)
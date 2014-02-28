import logging
import os
import re
from pythonthumbnail.compat import string_type
from pythonthumbnail.helpers import tokey, serialize
from pythonthumbnail.images import ImageFile
from pythonthumbnail.parsers import parse_geometry


logger = logging.getLogger(__name__)

EXTENSIONS = {
    'JPEG': 'jpg',
    'PNG': 'png',
}


class ThumbnailBackend(object):
    """
    The main class for sorl-thumbnail, you can subclass this if you for example
    want to change the way destination filename is generated.
    """

    default_options = {
        'format': 'JPEG',
        'quality': 100,
        'colorspace': 'RGB',
        'upscale': True,
        'crop': False,
        'cropbox': None,
        'rounded': None,
        'padding': False,
        'padding_color': '#ffffff',
    }

    extra_options = (
        ('progressive', 'THUMBNAIL_PROGRESSIVE'),
        ('orientation', 'THUMBNAIL_ORIENTATION'),
        ('blur', 'THUMBNAIL_BLUR'),
    )

    def __init__(self, storage, engine, thumbnail_prefix='cache/', thumbnail_format='JPEG'):
        self.storage = storage
        self.engine = engine
        self.thumbnail_prefix = thumbnail_prefix
        self.thumbnail_format = thumbnail_format

    def file_extension(self, file_):
        return os.path.splitext(file_.name)[1].lower()

    def _get_format(self, file_):
        file_extension = self.file_extension(file_)

        if file_extension == '.jpg' or file_extension == '.jpeg':
            return 'JPEG'
        elif file_extension == '.png':
            return 'PNG'
        else:
            return self.thumbnail_format

    def get_thumbnail(self, file_, geometry_string, **options):
        """
        Returns thumbnail as an ImageFile instance for file with geometry and
        options given. First it will try to get it from the key value store,
        secondly it will create it.
        """
        logger.debug('Getting thumbnail for file [%s] at [%s]', file_,
                     geometry_string)
        if file_:
            source = ImageFile(file_, storage=self.storage)
        else:
            return None

        for key, value in self.default_options.items():
            options.setdefault(key, value)

        name = self._get_thumbnail_filename(source, geometry_string, options)
        thumbnail = ImageFile(name, self.storage)
        try:
            source_image = self.engine.get_image(source)
        except IOError:
            # if settings.THUMBNAIL_DUMMY:
            #     return DummyImageFile(geometry_string)
            # else:
                # if S3Storage says file doesn't exist remotely, don't try to
                # create it and exit early.
                # Will return working empty image type; 404'd image
            logger.warn('Remote file [%s] at [%s] does not exist', file_, geometry_string)
            return thumbnail

        # We might as well set the size since we have the image in memory
        image_info = self.engine.get_image_info(source_image)
        options['image_info'] = image_info
        size = self.engine.get_image_size(source_image)
        source.set_size(size)
        try:
            self._create_thumbnail(source_image, geometry_string, options,
                                   thumbnail)
        finally:
            self.engine.cleanup(source_image)

        return thumbnail

    def delete(self, file_, delete_file=True):
        """
        Deletes file_ references in Key Value store and optionally the file_
        it self.
        """
        image_file = ImageFile(file_)
        if delete_file:
            image_file.delete()

    def _create_thumbnail(self, source_image, geometry_string, options,
                          thumbnail):
        """
        Creates the thumbnail by using default.engine
        """
        logger.debug('Creating thumbnail file [%s] at [%s] with [%s]',
                     thumbnail.name, geometry_string, options)
        ratio = self.engine.get_image_ratio(source_image, options)
        geometry = parse_geometry(geometry_string, ratio)
        image = self.engine.create(source_image, geometry, options)
        self.engine.write(image, options, thumbnail)
        # It's much cheaper to set the size here
        size = self.engine.get_image_size(image)
        thumbnail.set_size(size)

    def _get_thumbnail_filename(self, source, geometry_string, options):
        """
        Computes the destination filename.
        """
        key = tokey(source.key, geometry_string, serialize(options))
        # make some subdirs
        path = '%s/%s/%s' % (key[:2], key[2:4], key)
        return '%s%s.%s' % (self.thumbnail_prefix, path,
                            EXTENSIONS[options['format']])

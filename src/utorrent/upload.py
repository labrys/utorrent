# code copied from http://www.doughellmann.com/PyMOTW/urllib2/


import itertools
import mimetypes
# pylint: disable-next=import-private-name
from email.generator import _make_boundary as choose_boundary


class MultiPartForm:
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = choose_boundary()

    def get_content_type(self):
        return f'multipart/form-data; boundary={self.boundary}'

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))

    def add_file(self, fieldname, filename, file_handle, mimetype=None):
        """Add a file to be uploaded."""
        body = file_handle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))

    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.
        parts = []
        part_boundary = '--' + self.boundary

        # Add the form fields
        parts.extend(
            [
                part_boundary,
                f'Content-Disposition: form-data; name="{name}"',
                '',
                value,
            ]
            for name, value in self.form_fields
        )

        # Add the files to upload
        parts.extend(
            [
                part_boundary,
                f'Content-Disposition: file; name="{field_name}"; filename="{filename}"',
                f'Content-Type: {content_type}',
                '',
                body,
            ]
            for field_name, filename, content_type, body in self.files
        )

        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)

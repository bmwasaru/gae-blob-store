import os

from google.appengine.api import users
import functools

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import jinja2
import webapp2

from models import UserPhoto

upload_url_rpc = blobstore.create_upload_url_async('/upload')
upload_url = upload_url_rpc.get_result()
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


def login_required(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.get_current_user:
            self.redirect(self.get_login_url())
            return
        else:
            return method(self, *args, **kwargs)
        return wrapper


class BaseHandler(webapp2.RequestHandler):

    def get_current_user(self):
        user = users.get_current_user().user_id()
        return user

    def get_login_url(self):
        return users.create_login_url(self.request.uri)


class PhotoUploadFormHandler(BaseHandler):

    @login_required
    def get(self):
        template = jinja_env.get_template('main.html')
        template_context = {'upload_url': upload_url}
        self.response.out.write(
            template.render(template_context))


class PhotoUploadHandler(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):

    @login_required
    def post(self):
        try:
            upload = self.get_uploads()[0]
            user_photo = UserPhoto(
                user=self.get_current_user,
                blob_key=upload.key())
            user_photo.put()
            self.redirect('/view/%s' % upload.key())
        except:
            self.error(500)


class ViewPhotoHandler(blobstore_handlers.BlobstoreDownloadHandler):

    @login_required
    def get(self, photo_key):
        if not blobstore.get(photo_key):
            self.error(404)
        else:
            self.send_blob(photo_key)


app = webapp2.WSGIApplication([
    ('/', PhotoUploadFormHandler),
    ('/upload_photo', PhotoUploadHandler),
    ('/view/([^/]+)?', ViewPhotoHandler),
], debug=True)

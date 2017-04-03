import hmac
import hashlib
from django.conf import settings


class MediathreadAuthenticator(object):
    def __init__(self, d):
        self.nonce = d.get('nonce', '')
        self.hmc = d.get('hmac', '')
        self.set_course = d.get('set_course', '')
        self.username = d.get('as')
        self.redirect_to = d.get('redirect_url', '')

    def is_valid(self):
        verify = hmac.new(
            settings.MEDIATHREAD_SECRET,
            '%s:%s:%s' % (self.username, self.redirect_to,
                          self.nonce),
            hashlib.sha1
        ).hexdigest()
        return verify == self.hmc

from django.db import models


class StreamLog(models.Model):
    filename = models.TextField(blank=True)
    remote_addr = models.TextField(blank=True)
    offset = models.TextField(blank=True)
    referer = models.TextField(blank=True)
    user_agent = models.TextField(blank=True)
    # how they were authenticated: cookie, url hash, or public
    access = models.TextField(blank=True)
    request_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-request_at']

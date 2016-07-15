import json
import os.path
import re


class SNSMessageError(Exception):
    pass


class Record(object):
    def __init__(self, d):
        self._d = d

    def event_source(self):
        return self._d['eventSource']

    def event_name(self):
        return self._d['eventName']

    def s3_bucket_name(self):
        return self._d['s3']['bucket']['name']

    def s3_bucket_arn(self):
        return self._d['s3']['bucket']['arn']

    def s3_bucket_key(self):
        return self._d['s3']['object']['key']

    def is_directory(self):
        return self.s3_bucket_key().endswith("/")

    def title(self):
        """ come up with a reasonable title based on the filename/key

        basically, strip off extension and directory info and convert
        non-alphanums to spaces.
        """
        fname = self.s3_bucket_key()
        base = os.path.basename(fname)
        title = os.path.splitext(base)[0]
        return re.sub(r"[_\W]+", " ", title)


class SNSMessage(object):
    def __init__(self, message):
        self._raw_message = message
        try:
            self._d = json.loads(message)
            self._payload = json.loads(self._d["Message"])
            self._records = self._payload["Records"]
        except ValueError:
            raise SNSMessageError()
        except KeyError:
            raise SNSMessageError()

    def message_type(self):
        return self._d['Type']

    def subject(self):
        return self._d['Subject']

    def topic(self):
        return self._d['TopicArn']

    def records(self):
        return [Record(r) for r in self._records]

import json


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

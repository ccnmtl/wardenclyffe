"""
most of this just comes straight from Google's sample code:

https://developers.google.com/youtube/v3/code_samples/python#upload_a_video

with a few improvements and simplifications.

"""

from django.conf import settings

import httplib2
import httplib
import random
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error, IOError, httplib.NotConnected,
    httplib.IncompleteRead, httplib.ImproperConnectionState,
    httplib.CannotSendRequest, httplib.CannotSendHeader,
    httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


class YTAuthError(Exception):
    pass


def get_authenticated_service(args):
    storage = Storage(settings.OAUTH_STORAGE_PATH)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        raise YTAuthError

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


class Args(object):
    pass


def get_credentials():
    """ do the oauth dance to get new credentials file """
    args = Args()
    args.logging_level = 'DEBUG'
    args.noauth_local_webserver = 'http://localhost:8000/'
    flow = flow_from_clientsecrets(
        settings.YOUTUBE_CLIENT_SECRETS_FILE,
        # it complains if you don't set something as the redirect_uri,
        # even though it's not used
        redirect_uri="http://localhost:8000/",
        scope=YOUTUBE_UPLOAD_SCOPE)

    storage = Storage("youtube_oauth.json")
    credentials = run_flow(flow, storage, args)
    return credentials


def initialize_upload(youtube, options):
    tags = None
    if options.keywords:
        tags = options.keywords

    body = dict(
        snippet=dict(
            title=options.title,
            description=options.description,
            tags=tags,
            categoryId=options.category
        ),
        status=dict(
            privacyStatus=options.privacyStatus
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()), body=body,
        # The chunksize parameter specifies the size of each chunk of
        # data, in bytes, that will be uploaded at a time. Set a
        # higher value for reliable connections as fewer chunks lead
        # to faster uploads. Set a lower value for better recovery on
        # less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that
        # the entire file will be uploaded in a single HTTP
        # request. (If the upload fails, it will still be retried
        # where it left off.) This is usually a best practice, but if
        # you're using Python older than 2.6 or if you're running on
        # App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )
    return resumable_upload(insert_request)


# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    youtube_id = None
    while response is None:
        try:
            print "Uploading file..."
            status, response = insert_request.next_chunk()
            if 'id' in response:
                print("Video id '%s' was successfully uploaded."
                      % response['id'])
                youtube_id = response['id']
            else:
                exit("The upload failed with an unexpected response: %s"
                     % response)
        except HttpError, e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (
                    e.resp.status, e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS, e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print error
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print "Sleeping %f seconds and then retrying..." % sleep_seconds
            time.sleep(sleep_seconds)
    return youtube_id

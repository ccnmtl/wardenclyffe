Wardenclyffe is a Django-based tool for orchestrating asynchronous workflows. The current implementation focuses on managing, encoding, and publishing audio/video/multimedia files. Wardenclyffe was eveloped at the Columbia
Center for New Media Teaching and Learning (http://ccnmtl.columbia.edu).

For a breif whitepaper on the history and origins of Wardenclyffe, see

[KINO and Wardenclyffe: A framework for encoding, managing, and publishing web video](https://docs.google.com/document/d/1Wux_2tpNgjt9wA7I-ZoVNdA6Eoxof3d3r7e3bx8WOlM/edit?usp=sharing)

Wardenclyffe currently uses Apple's PodCast Producer for video encodings (http://ccnmtl.columbia.edu/compiled/released/how_to_get_pcp_on_the_web.html for more details), but we are currently working to support Amazon's Elastic Transcoder.

== Requirements ==

* Python (2.6 preferred. could probably be made to work with others)
* postgres (8+)
* rabbitmq
* tahoe
* podcast producer
* apache for production deployment
* mplayer (for video frame and metadata extraction)

== Assumptions (how we tend to deploy): ==

* code is checked out into /var/www/wardenclyffe/wardenclyffe/
* /var/www/wardenclyffe/uploads/ exists
* everything under /var/www/wardenclyffe is owned by user 'pusher'

== How to get it running. ==

    cd /var/www/wardenclyffe/wardenclyffe/
    # initialize the database
    make install
    # run webserver
    make runserver
    # in another terminal, cd to the same directory and run
    ./manage.py celeryd   # starts up the celery server

That probably won't work directly, but it's worth a shot. Wardenclyffe
currently expects a lot of configuration variables for the various
services that it talks to. I'm not sure how well it will work without
working values set for most/all of these:

    BROKER_URL
    SENTRY_KEY
    TMP_DIR = '/var/tmp/wardenclyffe'
    WATCH_DIRECTORY = "/var/tmp/wardenclyffe/watch_dir/"
    PCP_BASE_URL
    PCP_USERNAME
    PCP_PASSWORD
    PCP_WORKFLOW
    MEDIATHREAD_BASE
    MEDIATHREAD_SECRET
    MEDIATHREAD_POST_URL
    MEDIATHREAD_PCP_WORKFLOW
    ZENCODER_API_KEY
    YOUTUBE_EMAIL
    YOUTUBE_PASSWORD
    YOUTUBE_SOURCE
    YOUTUBE_DEVELOPER_KEY
    YOUTUBE_CLIENT_ID
    VITAL_SECRET

Certainly those individual parts won't work, but I'm not sure if the
whole thing will run at all without them at least set to dummy variables.
[![Build Status](https://travis-ci.org/ccnmtl/wardenclyffe.svg?branch=master)](https://travis-ci.org/ccnmtl/wardenclyffe)

Wardenclyffe is a Django-based tool for orchestrating asynchronous
workflows. The current implementation focuses on managing, encoding,
and publishing audio/video/multimedia files. Wardenclyffe was eveloped
at the Columbia Center for New Media Teaching and Learning
(http://ccnmtl.columbia.edu).

For a breif whitepaper on the history and origins of Wardenclyffe, see

[KINO and Wardenclyffe: A framework for encoding, managing, and publishing web video](https://docs.google.com/document/d/1Wux_2tpNgjt9wA7I-ZoVNdA6Eoxof3d3r7e3bx8WOlM/edit?usp=sharing)

## Development with docker-compose

You will need Docker and docker-compose
[installed](https://docs.docker.com/compose/install/).

Then, in a checked out version of this project, you can just run

    $ docker-compose up

And you should soon have a running instance on port 8000.

If this is the first time you've run it (or database schema changes
have happened since the last time you ran it), you'll need to
initialize the database by running:

    $ docker-compose run web python manage.py migrate --settings=wardenclyffe.settings_compose

## Requirements

* Python (2.7 preferred. could probably be made to work with others)
* postgres (8+)
* rabbitmq
* podcast producer
* apache for production deployment
* ffmpeg (for video frame and metadata extraction)

## Assumptions (how we tend to deploy): ##

* code is checked out into /var/www/wardenclyffe/wardenclyffe/
* /var/www/wardenclyffe/uploads/ exists
* everything under /var/www/wardenclyffe is owned by user 'pusher'

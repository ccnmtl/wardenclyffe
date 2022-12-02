[![Actions Status](https://github.com/ccnmtl/wardenclyffe/workflows/build-and-test/badge.svg)](https://github.com/ccnmtl/wardenclyffe/actions)


Wardenclyffe is a Django-based tool for orchestrating asynchronous
workflows. The current implementation focuses on managing, encoding,
and publishing audio/video/multimedia files. Wardenclyffe was developed
at Columbia University's Center for Teaching and Learning
(http://ctl.columbia.edu).

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

Or just

    $ make compose-migrate

You can also do:

    $ make compose-install

which will do the migrate, and also set up the waffle flags that you
probably want (that only needs to be done once at the beginning).

If you plan on actually doing anything with the AWS video processing
side of things, you will need to set up a
`wardenclyffe/local_settings.py` that has your AWS credentials and the
various S3/ETS settings. Similarly with Surelink, you will need to set
up its expected variables.

### Caveats/Issues

docker-compose is convenient but there are still some rough spots that
you'll need to deal with:

* the django runserver ("web") container sometimes starts too quickly, before
  the postgres container is able to accept connections. Usually just a
  `C-c` and try again will handle it.
* the "web" container will do the usual thing and restart the django
  app automatically when files change just like we're used
  to. However, the celery container doesn't. Fair warning that you
  will probably pull some hair out over this at some point when you
  change something inside a task and can't figure out why it's not
  working.
* for CAS, you will need to run this behind nginx+ssl as usual. Make
  sure to set `client_max_body_size` to something reasonable so you
  can upload videos.

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

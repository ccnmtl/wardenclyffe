[![Actions Status](https://github.com/ccnmtl/wardenclyffe/workflows/build-and-test/badge.svg)](https://github.com/ccnmtl/wardenclyffe/actions)


Wardenclyffe is a Django-based tool for orchestrating asynchronous
workflows. The current implementation focuses on managing, encoding,
and publishing audio/video/multimedia files. Wardenclyffe was developed
at Columbia University's Center for Teaching and Learning
(http://ctl.columbia.edu).

For a brief whitepaper on the history and origins of Wardenclyffe, see:
[KINO and Wardenclyffe: A framework for encoding, managing, and publishing web video](https://docs.google.com/document/d/1Wux_2tpNgjt9wA7I-ZoVNdA6Eoxof3d3r7e3bx8WOlM/edit?usp=sharing)

## Requirements

* Python 3.11
* postgres 14+
* rabbitmq
* podcast producer
* apache for production deployment
* ffmpeg (for video frame and metadata extraction)

## Assumptions (how we tend to deploy): ##

* code is checked out into /var/www/wardenclyffe/wardenclyffe/
* /var/www/wardenclyffe/uploads/ exists
* everything under /var/www/wardenclyffe is owned by user 'pusher'

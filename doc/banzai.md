# Banzai Design

"Banzai" is the codename for the new pipeline/workflow model for
Wardenclyffe. (Named for the
[Banzai Pipeline](https://en.wikipedia.org/wiki/Banzai_Pipeline)).

## Goals

Banzai is an overhauling of the workflow system to clean up inter-step
dependency handling and enable through-the-web creation and
modification of workflows by non-programmers.

## Background

One of the big issues that WC was designed to address was sequencing a
number of steps that are involved in encoding and serving a video
file, taking advantage of parallelism where possible while enforcing
dependencies between the steps and dealing with the differences
between steps that are performed directly by Wardenclyffe and steps
that are performed by an external service (PCP or Elastic
Transcoder). Eg, a video file that is uploaded to Mediathread goes
through the following:

* an Elastic Transcoder job is started
* metadata is extracted from the video (to determine type, aspect
ratio, etc)
* a poster frame is set from one of the extracted thumbnails
* the encoded video is copied to the h264 secure directory on Cunix servers
* Mediathread is notified of the new video

The final step of submitting the video info to Mediathread can't be
initiated until 1) metadata extraction has completed, 2) a poster
frame has been set, and 3) the encoded video has been uploaded to
cunix. The poster frame and upload to cunix steps can't be initiated
until ET has finished encoding the video.

Many video uploads can be running concurrently and each of those steps
can take more or less time than expected. Eg, it's unusual, but on
occasion the ET encode for a video finishes and the video is uploaded
to cunix before the extract metadata step has had a chance to
complete.

A video that isn't going to Mediathread goes through the same set of
steps, minus the Mediathread submit at the end.

An audio file that's uploaded to Mediathread goes through a very
similar process, except that there's an extra step at the beginning
that converts the audio file to a video file before the other steps
can begin.

A video destined for Youtube will still go through the ET encode step
(if only so we can get a poster frame to put into WC's UI), but there
is no need for WC to wait for that to finish before uploading the
video to Youtube, so that can happen in parallel.

Clearly, there are a lot of steps that overlap between each of those
use-cases and it would be foolish to hard-code each use-case
seperately. WC has largely avoided that and allows us to string
together the individual steps to address different use-cases.

However, WC's current architecture is limited in the following ways:

1) much of the inter-step dependency handling is ad-hoc and
fragile. The common use-cases are fairly well tested at this point,
but changing a workflow (eg, adding a step to add a bumper or
watermark to videos) is a risky job and usually involves some
breakage and manual testing.

2) workflows to handle new use-cases can only be implemented by
developers by modifying the code.

We would like to place more power in the hands of the users (well, the
video team, at least) to define new workflows to address new use-cases
without having to get developers involved. That can't be done with the
current architecture.

## Overview

The architecture is deeply influenced by
[Petri Nets](https://en.wikipedia.org/wiki/Petri_net). I won't use PN
terminology here, prefering slightly less theoretical terminology, but
if you're familiar with the model, the influences should be pretty
clear.

At the lowest level, we have a `task`, which corresponds more or less
exactly to a Celery `task` along with the boilerplate for passing in
parameters, etc. Tasks are implemented in Python code and are written
by programmers. The code is part of the WC codebase. Really no way
around that (I'm not yet interested in Rolf-style code entry through
the browser).

We then define a `Step`, which consists of a `task` along with three
sets of `Event`s. One set is prerequisite `Event`s, one set is success
`Event`s, and one is failure `Event`s.

An `Event` is simply an identifiable, distinguishable type.

A given `Step` will execute its task when (and only when) all of its
prerequisite `Event`s have been seen. When it completes, if
successful, the success `Event`s will be fired. If it fails, the
failure `Event`s are fired instead.

Now we can define a `Workflow`, which is simply a set of `Step`s. It
implicitly would also contain a set of `Event`s (the ones that the
included `Step`s are triggered by and produce). Note that there is no
explicit ordering of `Step`s within the `Workflow`. Ordering is
implicit by the `Event`s involved.

With a pre-defined set of generic `Step`s and their respective
`Event`s, it's pretty easy to imagine a user creating a new `Workflow`
through the web by selecting the `Step`s. This `Workflow` can then be
named, associated with `Collection`s or drop buckets, etc.

That's all fairly abstract. You can think of the `Workflow`, `Step`s,
and `Event`s as "classes" that simply define behavior. When a video is
actually uploaded, WC "instantiates" them, associating them with the
`Video` object, and procedes to execute them. Since we need to be able
to monitor and observe the process as it executes, we need to have
terms for the concrete things that are created and run.

Let's introduce a `Pipeline`, which is an instantiation of a
`Workflow` associated with a `Video`. This is created when a video is
uploaded, or when a user manually submits an existing `Video` to a
specific `Workflow`. We can track general state metadata for the
`Pipeline`: time started, time completed, status (running, aborted,
etc) and use it to hang temporary metadata off (eg, which Mediathread
course the video will eventually go to or the ET job ID that was
started)

Let's go through a more detailed example, seeing exactly what happens
in this model when a video is uploaded to the Mediathread `Workflow`.

First, we have to define the `Step`s that are in the `Workflow`:

* extract metadata
** prereq events: `START`
** success events: `metadata extracted`
** failure events: `failed`
* create Elastic Transcode Job
** prereq events: `START`
** success events: `ET Job created`
** failure events: `failed`
* pull down thumbnails
** prereq events: `ET Job finished`
** success events: `poster created`
** failure events: `failed`
* copy from S3 output bucket to cunix
** prereq events: `ET Job finished`
** success events: `uploaded to cunix`
** failure events: `failed`
* mediathread submit
** prereq events: `metadata extracted`, `poster created`, `uploaded to cunix`
** success events: `submitted to mediathread`
** failure events: `failed`
* email user (success)
** prereq events: `submitted to mediathread`
** success events: `OK`
** failure events: `failed`
* email user (failure)
** prereq events: `START`
** success events: `FAIL`
** failure events: `FAIL`

`START`, `OK`, and `FAIL` are special `Event`s that are either created
or handled directly by WC.

* a `Video` object is created (as currently happens)
* a `Pipeline` is created associated with the `Video` and `Workflow`.
* additional metadata is attached to that `Pipeline`: mediathread
  course id, user uploading the video, S3 key for the source video
  that was uploaded
* For each `Step` associated with the Mediathread `Workflow`, `Step`
  objects are instantiated, each associated with the `Pipeline`, each
  with their status set to `blocked`, since all steps require an
  `Event` to trigger them and there are not yet any here.
* a `START` `Event` is created (and associated with the `Pipeline`).
* whenever WC sees a new `Event`, it goes through all the `Step`s in
  the `Pipeline` and checks if they are waiting on that `Event`
  type. If so (and it's seen all the `Event`s that the `Step` is
  waiting on), it changes the `Step`'s status to `ready` and adds its
  `task` to the Celery Job Queue.
* When Celery runs a `task`, it changes the associated `Step`'s status
  to `running` and executes the code. Assuming success, it changes the
  `Step`s status to `complete` and fires off any events in that
  `Step`'s list of success `Event`s. If it fails, it sets the `Step`'s
  status to `failed` and fires the failure `Event`s instead.
* so, when WC fires off the initial `START` event, `extract metadata`
  and `create Elastic Transcode Job` both become `ready` and their
  tasks go into the Queue.
* assuming `extract metadata` finishes first. A `metadata extracted`
  `Event` is fired. `mediathread submit` is blocked on that event, but
  it's also blocked on `poster created` and `uploaded to cunix`, which
  it has not seen yet, so it stays blocked.
* now, notice that `create Elastic Transcode job` generates an `ET job
  created` `Event`, but no `Step`s are looking for that. Instead,
  they're looking for `ET job finished`. This is because ET is its own
  system with its own queue and it notifies us of completion through a
  separate SNS endpoint. That endpoint, when it gets hit, simply finds the
  `Pipeline` that corresponds to the ET job, adds a bit of metadata
  with the S3 key of the encoded file, and then fires off an `ET job
  finished` event.
* when that `ET job finished` `Event` is processed, `pull down
  thumbnails` and `copy from S3 output bucket to cunix` both become
  `ready` and their tasks are enqueued.
* as each of those finish, again `submit to mediathread` will be
  examined since it depends on all those `Event`s. Only when the last
  of them comes through will it become `ready`.
* eventually `email user (success)` will run and emit an `OK`, which
  WC knows it can safely ignore.
* if any of the steps fail, they would emit a `failed` event and
  `email user (fail)` would execute, letting the original user know
  that something went wrong. Then `FAIL` would be emitted and WC would
  mark the entire `Pipeline` as failed and block the processing of any
  other `Event`s or `Step`s in the `Pipeline`. If we wanted more
  complicated error handling, it would just be a matter of defining
  more granular events than `failed` and creating `Step`s to handle
  them (perhaps some failures could be corrected for).

That should give you a sense of how this all works.

Some advantages that may have been glossed over:

* the mechanism of processing `Event`s and triggering `Step`s is
  incredibly generic but supports very complicated workflows. It
  should be straightforward to implement and have it nicely abstracted
  out from the details of how our videos are currently processed,
  allowing it to support nearly any future workflows and external
  integrations we might need.
* async external integrations become a matter of setting up an
  endpoint that just generates an `Event` of a fixed type. It doesn't
  need to know anything else about the system, which keeps it flexible
  for using in all kinds of different workflows.
* It also becomes straightforward for non-programmer users to assemble
  a new `Workflow` from a pool of available `Step`s. That can be done
  through the web. If we wanted to get fancy, it wouldn't be that
  difficult to eg, draw a Petri Net style diagram of the workflow,
  warn the user if the `Workflow` is incomplete (eg, `Step`s included
  that depend on `Event`s that no other included `Step` can generate,
  etc.)

## Open Issues

* Are there actually any use-cases for specific failure events? Ie,
  would we ever need to do anything differently if Step A fails vs
  Step B? Or would we always just abort the whole pipeline (in which
  case, we might as well just have a single implicit 'fail' `Event`
  that any `Step` can trigger)? Is that flexibility that we need? Or
  will it just add complexity?

* I've lazily re-used the term `Step` both for the abstract thing that
  is just a mapping of a `task` to input and output `Event`s and a
  concrete instance that maps the abstract `Step` to a `Pipeline`. It
  would be nice to have abstract/concrete terms analogous to how
  `Workflow` and `Pipeline` are defined. "`StepType`", perhaps? I do
  think of it as analogous to a type in a programming language, but
  "type" in general is annoying since you have to be really careful
  about not using it directly in Python and SQL. There's actually the
  same problem with `Event`, but less troublesome because an
  "EventType" can really just be a string value.

## Migration Strategy

Ie, how do we get from where WC currently is, to this new architecture
without breaking everything in the meantime?

This is a pretty disruptive change, since it replaces some pretty core
functionality.

I would probably start by implementing most of the `Event` and `Step`
triggering and processing code on its own. Being very abstract, that
code should be very self-contained and testable.

Once that is reliable on its own, we would integrate it with the video
upload in a couple phases:

* first, a separate upload form, not visible to regular users. Upload
  there and instead of the current WC `Operations`, it kicks off a
  `Pipeline`. We could test quite a bit in production there with dummy
  `Step`s that don't really do much, slowly building up to real
  `Workflow`s. UI for through-the-web `Workflow` definition could go
  on in parallel hidden behind a feature flag.
* once we're happy with that, we set up a feature flag to kick of a
  `Pipeline` in parallel with the current version when a user uploads
  any video. Again, probably hiding it from most users (leaving off
  the final email confirmation `Step`, eg). That lets us test on
  "real" data while the current system is still in place.
* eventually, we could change the feature flag to then toggle between
old and new approaches and roll it out internally, then fully.
* finally, once everyone is using the new version, we remove the
  feature flag and clean out the old code.


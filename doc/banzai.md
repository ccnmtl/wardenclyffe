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
but changing a workflow is a risky job and usually involves some
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

[TODO]

## Open Issues

* Are there actually any use-cases for specific failure events? Ie,
  would we ever need to do anything differently if Step A fails vs
  Step B? Or would we always just abort the whole pipeline (in which
  case, we might as well just have a single implicit 'fail' `Event`
  that any `Step` can trigger)? Is that flexibility that we need? Or
  will it just add complexity?


[TODO]

## Migration Strategy

Ie, how do we get from where WC currently is, to this new architecture
without breaking everything in the meantime?

[TODO]

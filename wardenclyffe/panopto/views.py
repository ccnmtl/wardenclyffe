# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls.base import reverse
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView
from django_statsd.clients import statsd

from wardenclyffe.main.models import Collection, Video
from wardenclyffe.main.views import enqueue_operations
from wardenclyffe.mediathread.auth import MediathreadAuthenticator
from wardenclyffe.mediathread.views import AuthenticatedNonAtomic
from wardenclyffe.panopto.forms import CollectionSubmitForm, VideoSubmitForm


def submit_video_to_panopto(user, video, folder_id, viewed=False):
    statsd.incr("panopto.submit")

    if viewed and video.streamlogs().count() < 1:
        return False

    if video.has_s3_source() or video.has_s3_transcoded():
        operations = [
            video.make_pull_from_s3_and_upload_to_panopto_operation(
                video.id, folder_id, user)
        ]
        enqueue_operations(operations)
    elif video.cuit_file():
        operations = [
            video.make_pull_from_cunix_and_upload_to_panopto_operation(
                video.id, folder_id, user)
        ]
        enqueue_operations(operations)


class VideoSubmitView(AuthenticatedNonAtomic, FormView):
    form_class = VideoSubmitForm
    template_name = 'panopto/video_submit.html'

    def get_video(self):
        pk = self.kwargs.get('pk', None)
        return get_object_or_404(Video, id=pk)

    def get_context_data(self, **kwargs):
        context = FormView.get_context_data(self, **kwargs)
        context['video'] = self.get_video()
        return context

    def form_valid(self, form):
        video = self.get_video()
        submit_video_to_panopto(
            self.request.user, video,
            form.cleaned_data['folder_id'])

        messages.add_message(
            self.request, messages.INFO,
            '{} was submitted to Panopto.'.format(video.title))

        return FormView.form_valid(self, form)

    def get_success_url(self):
        return reverse('video-details',
                       kwargs={'pk': self.kwargs.get('pk', None)})


class CollectionSubmitSuccessView(TemplateView):
    template_name = 'panopto/collection_submit_success.html'

    def get_collection(self):
        pk = self.kwargs.get('pk', None)
        return get_object_or_404(Collection, id=pk)

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context['collection'] = self.get_collection()
        return context


class CollectionSubmitView(AuthenticatedNonAtomic, FormView):
    form_class = CollectionSubmitForm
    template_name = 'panopto/collection_submit.html'

    def get_collection(self):
        pk = self.kwargs.get('pk', None)
        return get_object_or_404(Collection, id=pk)

    def get_initial(self):
        initial = super(CollectionSubmitView, self).get_initial()
        initial['collection'] = self.kwargs.get('pk', None)
        return initial

    def get_context_data(self, **kwargs):
        context = FormView.get_context_data(self, **kwargs)
        context['collection'] = self.get_collection()
        return context

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        collection = form.cleaned_data['collection']
        folder_id = form.cleaned_data['folder_id']
        allow_reupload = form.cleaned_data['allow_reupload']

        for video in collection.video_set.all():
            if allow_reupload or not video.has_panopto_source():
                submit_video_to_panopto(self.request.user, video, folder_id,
                                        form.cleaned_data['viewed'])

        return FormView.form_valid(self, form)

    def get_success_url(self):
        return reverse('panopto-collection-success-submit',
                       kwargs={'pk': self.kwargs.get('pk', None)})


@transaction.non_atomic_requests()
class APIPanoptoConversion(View):

    def post(self, request, *args, **kwargs):
        # for this situation, authenticator expects
        # the usual `hmac` and `nonce`, plus
        # `as` to give a username (WC needs to associate operations with users)
        # and `redirect_to` set to the video_id
        # (that prevents the token from being intercepted and changed
        # to migrate a different video than specified)

        authenticator = MediathreadAuthenticator(request.POST)
        if not authenticator.is_valid():
            statsd.incr("mediathread.auth_failure")
            return HttpResponse("invalid authentication token")

        user, created = User.objects.get_or_create(
            username=authenticator.username)
        if created:
            statsd.incr("mediathread.user_created")

        # remember, we're overloading the `redirect_to` field
        pk = authenticator.redirect_to
        video = get_object_or_404(Video, pk=pk)
        if video.has_panopto_source():
            return HttpResponse('migration completed')

        folder = request.POST.get('folder', '')

        video.create_mediathread_update()

        submit_video_to_panopto(user, video, folder)
        return HttpResponse('ok')

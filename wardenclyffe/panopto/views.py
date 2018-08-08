# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls.base import reverse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django_statsd.clients import statsd

from wardenclyffe.main.models import Collection, Video
from wardenclyffe.main.views import enqueue_operations
from wardenclyffe.mediathread.views import AuthenticatedNonAtomic
from wardenclyffe.panopto.forms import CollectionSubmitForm, VideoSubmitForm


def submit_video_to_panopto(user, video, folder_id):
    statsd.incr("panopto.submit")

    if video.has_s3_source():
        operations = [
            video.make_pull_from_s3_and_upload_to_panopto_operation(
                video.id, folder_id, user)
        ]
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
        folder_id = form.cleaned_data['folder_id']
        submit_video_to_panopto(self.request.user, video, folder_id)

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

        for video in collection.video_set.all():
            if not video.has_panopto_source():
                submit_video_to_panopto(self.request.user, video, folder_id)

        return FormView.form_valid(self, form)

    def get_success_url(self):
        return reverse('panopto-collection-success-submit',
                       kwargs={'pk': self.kwargs.get('pk', None)})

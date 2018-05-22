# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.urls.base import reverse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django_statsd.clients import statsd

from wardenclyffe.main.models import Collection
from wardenclyffe.main.views import enqueue_operations
from wardenclyffe.mediathread.views import AuthenticatedNonAtomic
from wardenclyffe.panopto.forms import CollectionSubmitForm


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

    def submit_video_to_panopto(self, video, folder_id):
        statsd.incr("panopto.submit")

        if video.has_s3_source():
            operations = [
                video.make_pull_from_s3_and_upload_to_panopto_operation(
                    video.id, folder_id, self.request.user)
            ]
        elif video.cuit_file():
            operations = [
                video.make_pull_from_cunix_and_upload_to_panopto_operation(
                    video.id, folder_id, self.request.user)
            ]

        enqueue_operations(operations)

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
            self.submit_video_to_panopto(video, folder_id)

        return FormView.form_valid(self, form)

    def get_success_url(self):
        return reverse('panopto-collection-success-submit',
                       kwargs={'pk': self.kwargs.get('pk', None)})

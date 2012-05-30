from wardenclyffe.main.models import Video, Collection, Server
from django import forms


class AddCollectionForm(forms.ModelForm):
    class Meta:
        model = Collection


class UploadVideoForm(forms.ModelForm):
    class Meta:
        model = Video


class AddServerForm(forms.ModelForm):
    class Meta:
        model = Server

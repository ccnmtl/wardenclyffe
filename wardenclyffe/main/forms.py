from wardenclyffe.main.models import Video, Collection, Server
from django import forms


class AddCollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        exclude = []


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        exclude = []


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        exclude = []


class EditCollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        exclude = []

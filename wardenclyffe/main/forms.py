from wardenclyffe.main.models import Video, Collection, Server
from django import forms


class AddCollectionForm(forms.ModelForm):
    class Meta:
        model = Collection


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server


class EditCollectionForm(forms.ModelForm):
    class Meta:
        model = Collection

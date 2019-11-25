from django import forms
from wardenclyffe.main.models import Collection, Video, Server, File


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


class AddVideoForm(forms.ModelForm):
    class Meta:
        model = Video
        exclude = ('collection', )


class AddFileForm(forms.ModelForm):
    class Meta:
        model = File
        exclude = ('video', )

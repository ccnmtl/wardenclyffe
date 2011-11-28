from wardenclyffe.main.models import Video, Series, Server
from django import forms

class AddSeriesForm(forms.ModelForm):
    class Meta:
        model = Series

class UploadVideoForm(forms.ModelForm):
    class Meta:
        model = Video

class AddServerForm(forms.ModelForm):
    class Meta:
        model = Server

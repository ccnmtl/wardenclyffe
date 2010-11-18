from models import Video
from django import forms

class UploadVideoForm(forms.Form):
    title = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 80, 'rows': 20}))
    source_file = forms.FileField()

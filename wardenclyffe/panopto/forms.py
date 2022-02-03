from django import forms

from wardenclyffe.main.models import Collection


class CollectionSubmitForm(forms.Form):
    collection = forms.ModelChoiceField(
        required=True,
        queryset=Collection.objects.all())

    folder_id = forms.CharField(required=True,
                                help_text="Panopto Folder UUID")

    viewed = forms.BooleanField(
        required=False,
        help_text="Only submit videos with views > 0")

    allow_reupload = forms.BooleanField(
        required=False,
        help_text="Allow videos to be reuploaded to Panopto")


class VideoSubmitForm(forms.Form):
    folder_id = forms.CharField(
        required=True,
        help_text="Panopto Folder UUID")

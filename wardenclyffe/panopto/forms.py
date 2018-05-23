from django import forms

from wardenclyffe.main.models import Collection


class CollectionSubmitForm(forms.Form):
    collection = forms.ModelChoiceField(
        required=True,
        queryset=Collection.objects.all())

    folder_id = forms.CharField(required=True,
                                help_text="Panoptop Folder UUID")


class VideoSubmitForm(forms.Form):
    folder_id = forms.CharField(required=True,
                                help_text="Panoptop Folder UUID")

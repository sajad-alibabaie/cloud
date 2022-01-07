from django import forms
import uuid
import os


class DocumentForm(forms.Form):
    file = forms.FileField(
                           label='Select a file',
                           help_text='max. 42 megabytes'
                           )

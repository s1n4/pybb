# coding: utf-8
from django import forms
from django.utils.translation import ugettext as _
from pybb.models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']


class TopicForm(forms.Form):
    name = forms.CharField(label=_('Topic name'))
    content = forms.CharField(label=_('Message'), widget=forms.Textarea)


class TopicDeleteForm(forms.Form):
    pass

# coding: utf-8
from django import forms

from pybb.models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']


class TopicForm(forms.Form):
    name = forms.CharField(label=u'Название темы')
    content = forms.CharField(label=u'Сообщение', widget=forms.Textarea)


class TopicDeleteForm(forms.Form):
    pass

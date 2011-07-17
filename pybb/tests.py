# -*- coding: utf-8 -*-
"""
PyBB test.

To run these tests you need django-webtest and lxml packages
"""
# These tests were developed with help of https://bitbucket.org/zeus/pybb/src/tip/pybb/tests.py
import time 

from django_webtest import WebTest
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings

from pybb.models import Category, Forum, Topic, Post, Profile


class PybbBaseTest(WebTest):
    def setUp(self):
        self.user = User.objects.create_user('foob', 'foob@foob.com', 'foob')
        self.category = Category.objects.create(name='main')
        self.forum = Forum.objects.create(name='Test forum', description='Forum for tests',
                                          category=self.category)
        self.topic = Topic.objects.create(name='Test topic', forum=self.forum, user=self.user)
        self.post = Post.objects.create(topic=self.topic, user=self.user, markup='bbcode',
                                        body='[b]Hello world![/b]')


class PybbUnitTest(PybbBaseTest):
    def test_automatic_profile_creation(self):
        profile = Profile.objects.get()
        self.assertEqual(self.user.pybb_profile, profile)

    def test_post_deletion(self):
        post = Post.objects.create(topic=self.topic, user=self.user, body='xyz',
                                   markup='bbcode')
        post.delete()
        self.assertEqual(Topic.objects.filter(pk=self.topic.pk).count(), 1)
        self.assertEqual(Forum.objects.filter(pk=self.topic.pk).count(), 1)

    def test_last_post_feature(self):
        self.assertEqual(self.topic.last_post, self.post)
        self.assertEqual(self.forum.last_post, self.post)

        post = Post.objects.create(topic=self.topic, user=self.user, body='xyz',
                                   markup='bbcode')
        topic = Topic.objects.get(pk=self.topic.pk)
        forum = Forum.objects.get(pk=self.forum.pk)
        self.assertEqual(topic.last_post, post)
        self.assertEqual(forum.last_post, post)

        post.delete()
        topic = Topic.objects.get(pk=self.topic.pk)
        forum = Forum.objects.get(pk=self.forum.pk)
        self.assertEqual(topic.last_post, self.post)
        self.assertEqual(forum.last_post, self.post)

    def test_last_post_deletion(self):
        self.assertEqual(Topic.objects.count(), 1)
        self.post.delete()
        self.assertEqual(Topic.objects.count(), 0)

    def test_topic_deletion(self):
        post = Post.objects.create(topic=self.topic, user=self.user, body='one', markup='bbcode')
        post = Post.objects.create(topic=self.topic, user=self.user, body='two', markup='bbcode')
        self.topic.delete()

        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(Forum.objects.count(), 1)

    def test_updated_fields(self):
        topic = Topic.objects.create(name='xtopic', forum=self.forum, user=self.user)
        post = Post.objects.create(topic=topic, user=self.user, body='one', markup='bbcode')

        topic = Topic.objects.get(pk=topic.pk)
        forum = Forum.objects.get(pk=self.forum.pk)
        self.assertEqual(topic.updated, post.created)
        self.assertEqual(forum.updated, post.created)


class PybbIntegrationTest(PybbBaseTest):
    def test_index_page(self):
        response = self.app.get(reverse('pybb_index'))
        self.assertTrue(self.forum.name in response)
        self.assertTrue(self.forum.get_absolute_url() in response)
        self.assertEqual(len(response.context['cats']), 1)


    def test_forum_page(self):
        response = self.app.get(self.forum.get_absolute_url())
        self.assertTrue(response.lxml.xpath('//a[@href="%s"]' % self.topic.get_absolute_url()))
        self.assertTrue(response.lxml.xpath('//title[contains(text(),"%s")]' % self.forum.name))
        self.assertFalse(response.lxml.xpath('//a[contains(@href,"?page=")]'))
        #self.assertFalse(response.context['is_paginated'])

    def test_user_page(self):
        response = self.app.get(self.user.pybb_profile.get_absolute_url())
        self.assertTrue(response.status_code==200)

    def test_profile_editing(self):
        response = self.app.get(reverse('pybb_profile_edit'), user=self.user)
        self.assertTrue(response.status_code==200)
        self.assertEqual(response.context['profile'], self.user.pybb_profile)
        form = response.form
        form['signature'] = 'test signature'
        response = form.submit().follow()
        self.assertTrue(response.status_code==200)
        self.app.get(self.post.get_absolute_url()).follow()
        self.assertContains(response, 'test signature')


    def test_pagination_and_topic_addition(self):
        self.forum.topics.all().delete()

        # Create as many topics as it could be on one page
        for x in xrange(settings.PYBB_FORUM_PAGE_SIZE):
            topic = Topic.objects.create(name='xyz', forum=self.forum, user=self.user)
        response = self.app.get(self.forum.get_absolute_url())
        self.assertEqual(len(response.context['page'].object_list), settings.PYBB_FORUM_PAGE_SIZE)
        self.assertEqual(response.context['page'].paginator.num_pages, 1)
        
        # Create additional topics, so all topics could not be fit on one page
        for x in xrange(2):
            topic = Topic.objects.create(name='xyz', forum=self.forum, user=self.user)

        pages, remainder = divmod(self.forum.topics.count(), settings.PYBB_FORUM_PAGE_SIZE)
        if remainder:
            pages += 1
        response = self.app.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['page'].paginator.num_pages, pages)

    def test_topic_title(self):
        response = self.app.get(self.topic.get_absolute_url())
        self.assertTrue(self.topic.name in response.lxml.xpath('//title')[0].text)

    def test_bbcode(self):
        response = self.app.get(self.topic.get_absolute_url())
        self.assertContains(response, self.post.body_html)

    #def test_read_tracking(self):
        #topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        #topic.save()
        #post = Post(topic=topic, user=self.user, body='one', markup='bbcode')
        #post.save()
        #client = Client()
        #client.login(username='zeus', password='zeus')
        ## Topic status
        #tree = html.fromstring(client.get(topic.forum.get_absolute_url()).content)
        #self.assertTrue(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.get_absolute_url()))
        ## Forum status
        #tree = html.fromstring(client.get(reverse('pybb:index')).content)
        #self.assertTrue(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        ## Visit it
        #client.get(topic.get_absolute_url())
        ## Topic status - readed
        #tree = html.fromstring(client.get(topic.forum.get_absolute_url()).content)
        ## Visit others
        #for t in topic.forum.topics.all():
            #client.get(t.get_absolute_url())
        #self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.get_absolute_url()))
        ## Forum status - readed
        #tree = html.fromstring(client.get(reverse('pybb:index')).content)
        #self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        ## Post message
        #response = client.post(reverse('pybb:add_post', args=[topic.id]), {'body': 'test tracking'}, follow=True)
        #self.assertContains(response, 'test tracking')
        ## Topic status - readed
        #tree = html.fromstring(client.get(topic.forum.get_absolute_url()).content)
        #self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.get_absolute_url()))
        ## Forum status - readed
        #tree = html.fromstring(client.get(reverse('pybb:index')).content)
        #self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        #post = Post(topic=topic, user=self.user, body='one', markup='bbcode')
        #post.save()
        #client.get(reverse('pybb:mark_all_as_read'))
        #tree = html.fromstring(client.get(reverse('pybb:index')).content)
        #self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        ## Empty forum - readed
        #f = Forum(name='empty', category=self.category)
        #f.save()
        #tree = html.fromstring(client.get(reverse('pybb:index')).content)
        #self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % f.get_absolute_url()))


    #def test_hidden(self):
        #client = Client()
        #category = Category(name='hcat', hidden=True)
        #category.save()
        #forum_in_hidden = Forum(name='in_hidden', category=category)
        #forum_in_hidden.save()
        #topic_in_hidden = Topic(forum=forum_in_hidden, name='in_hidden', user=self.user)
        #topic_in_hidden.save()

        #forum_hidden = Forum(name='hidden', category=self.category, hidden=True)
        #forum_hidden.save()
        #topic_hidden = Topic(forum=forum_hidden, name='hidden', user=self.user)
        #topic_hidden.save()

        #post_hidden = Post(topic=topic_hidden, user=self.user, body='hidden', markup='bbcode')
        #post_hidden.save()

        #post_in_hidden = Post(topic=topic_in_hidden, user=self.user, body='hidden', markup='bbcode')
        #post_in_hidden.save()

        
        #self.assertFalse(category.id in [c.id for c in client.get(reverse('pybb:index')).context['categories']])
        #self.assertTrue(client.get(category.get_absolute_url()).status_code==404)
        #self.assertTrue(client.get(forum_in_hidden.get_absolute_url()).status_code==404)
        #self.assertTrue(client.get(topic_in_hidden.get_absolute_url()).status_code==404)

        #self.assertNotContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())
        #self.assertNotContains(client.get(reverse('pybb:feed', kwargs={'url': 'topics'})), topic_hidden.get_absolute_url())
        #self.assertNotContains(client.get(reverse('pybb:feed', kwargs={'url': 'topics'})), topic_in_hidden.get_absolute_url())

        #self.assertNotContains(client.get(reverse('pybb:feed', kwargs={'url': 'posts'})), post_hidden.get_absolute_url())
        #self.assertNotContains(client.get(reverse('pybb:feed', kwargs={'url': 'posts'})), post_in_hidden.get_absolute_url())
        #self.assertTrue(client.get(forum_hidden.get_absolute_url()).status_code==404)
        #self.assertTrue(client.get(topic_hidden.get_absolute_url()).status_code==404)

        #client.login(username='zeus', password='zeus')
        #self.assertFalse(category.id in [c.id for c in client.get(reverse('pybb:index')).context['categories']])
        #self.assertNotContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())
        #self.assertTrue(client.get(category.get_absolute_url()).status_code==404)
        #self.assertTrue(client.get(forum_in_hidden.get_absolute_url()).status_code==404)
        #self.assertTrue(client.get(topic_in_hidden.get_absolute_url()).status_code==404)
        #self.assertTrue(client.get(forum_hidden.get_absolute_url()).status_code==404)
        #self.assertTrue(client.get(topic_hidden.get_absolute_url()).status_code==404)
        #self.user.is_staff = True
        #self.user.save()
        #self.assertTrue(category.id in [c.id for c in client.get(reverse('pybb:index')).context['categories']])
        #self.assertContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())
        #self.assertFalse(client.get(category.get_absolute_url()).status_code==404)
        #self.assertFalse(client.get(forum_in_hidden.get_absolute_url()).status_code==404)
        #self.assertFalse(client.get(topic_in_hidden.get_absolute_url()).status_code==404)
        #self.assertFalse(client.get(forum_hidden.get_absolute_url()).status_code==404)
        #self.assertFalse(client.get(topic_hidden.get_absolute_url()).status_code==404)

    #def test_inactive(self):
        #client = Client()
        #client.login(username='zeus', password='zeus')
        #client.post(reverse('pybb:add_post', args=[self.topic.id]), {'body': 'test ban'}, follow=True)
        #self.assertTrue(len(Post.objects.filter(body='test ban'))==1)
        #self.user.is_active = False
        #self.user.save()
        #client.post(reverse('pybb:add_post', args=[self.topic.id]), {'body': 'test ban 2'}, follow=True)
        #self.assertTrue(len(Post.objects.filter(body='test ban 2'))==0)

    #def get_csrf(self, form):
        #return form.xpath('//input[@name="csrfmiddlewaretoken"]/@value')[0]

    #def test_csrf(self):
        #client = Client(enforce_csrf_checks=True)
        #client.login(username='zeus', password='zeus')
        #response = client.post(reverse('pybb:add_post', args=[self.topic.id]), {'body': 'test csrf'}, follow=True)
        #self.assertFalse(response.status_code==200)
        #response = client.get(self.topic.get_absolute_url())
        #form = html.fromstring(response.content).xpath('//form[@class="post-form"]')[0]
        #token = self.get_csrf(form)
        #response = client.post(reverse('pybb:add_post', args=[self.topic.id]), {'body': 'test csrf', 'csrfmiddlewaretoken': token}, follow=True)
        #self.assertTrue(response.status_code==200)

    #def test_user_blocking(self):
        #user = User.objects.create_user('test', 'test@localhost', 'test')
        #self.user.is_superuser = True
        #self.user.save()
        #client = Client()
        #client.login(username='zeus', password='zeus')
        #self.assertTrue(client.get(reverse('pybb:block_user', args=[user.username]), follow=True).status_code==200)
        #user = User.objects.get(username=user.username)
        #self.assertFalse(user.is_active)

    #def test_ajax_preview(self):
        #client = Client()
        #client.login(username='zeus', password='zeus')
        #response = client.post(reverse('pybb:post_ajax_preview'), data={'data': '[b]test bbcode ajax preview[b]'})
        #self.assertContains(response, '<strong>test bbcode ajax preview</strong>')

    #def test_headline(self):
        #self.forum.headline = 'test <b>headline</b>'
        #self.forum.save()
        #client = Client()
        #self.assertContains(client.get(self.forum.get_absolute_url()), 'test <b>headline</b>')

    #def test_quote(self):
        #client = Client()
        #client.login(username='zeus', password='zeus')
        #response = client.get(reverse('pybb:add_post', args=[self.topic.id]), data={'quote_id': self.post.id, 'body': 'test tracking'}, follow=True)
        #self.assertTrue(response.status_code==200)
        #self.assertContains(response, self.post.body)

    #def test_edit_post(self):
        #client = Client()
        #client.login(username='zeus', password='zeus')
        #response = client.get(reverse('pybb:edit_post', args=[self.post.id]))
        #self.assertTrue(response.status_code==200)
        #tree = html.fromstring(response.content)
        #values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        #values['body'] = 'test edit'
        #response = client.post(reverse('pybb:edit_post', args=[self.post.id]), data=values, follow=True)
        #self.assertTrue(response.status_code==200)
        #self.assertContains(response, 'test edit')
        ## Check admin form
        #self.user.is_staff = True
        #response = client.get(reverse('pybb:edit_post', args=[self.post.id]))
        #self.assertTrue(response.status_code==200)
        #tree = html.fromstring(response.content)
        #values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        #values['body'] = 'test edit'
        #values['login'] = 'new_login'
        #response = client.post(reverse('pybb:edit_post', args=[self.post.id]), data=values, follow=True)
        #self.assertTrue(response.status_code==200)
        #self.assertContains(response, 'test edit')

    #def test_stick(self):
        #self.user.is_superuser = True
        #client = Client()
        #client.login(username='zeus', password='zeus')
        #self.assertTrue(client.get(reverse('pybb:stick_topic', args=[self.topic.id]), follow=True).status_code==200)
        #self.assertTrue(client.get(reverse('pybb:unstick_topic', args=[self.topic.id]), follow=True).status_code==200)

    #def test_delete_view(self):
        #post = Post(topic=self.topic, user=self.user, body='test to delete', markup='bbcode')
        #post.save()
        #client = Client()
        #client.login(username='zeus', password='zeus')
        #response = client.post(reverse('pybb:delete_post', args=[post.id]), follow=True)
        #self.assertTrue(response.status_code==200)
        ## Check that topic and forum exists ;)
        #self.assertTrue(Topic.objects.filter(id=self.topic.id).count()==1)
        #self.assertTrue(Forum.objects.filter(id=self.forum.id).count()==1)

        ## Delete topic
        #response = client.post(reverse('pybb:delete_post', args=[self.post.id]), follow=True)
        #self.assertTrue(response.status_code==200)
        #self.assertTrue(Post.objects.filter(id=self.post.id).count()==0)
        #self.assertTrue(Topic.objects.filter(id=self.topic.id).count()==0)
        #self.assertTrue(Forum.objects.filter(id=self.forum.id).count()==1)

    #def test_open_close(self):
        #self.user.is_superuser = True
        #self.user.save()
        #client = Client()
        #client.login(username='zeus', password='zeus')
        #response = client.get(reverse('pybb:close_topic', args=[self.topic.id]), follow=True)
        #self.assertTrue(response.status_code==200)
        #response = client.post(reverse('pybb:add_post', args=[self.topic.id]), {'body': 'test closed'}, follow=True)
        #self.assertTrue(response.status_code==403)
        #response = client.get(reverse('pybb:open_topic', args=[self.topic.id]), follow=True)
        #self.assertTrue(response.status_code==200)
        #response = client.post(reverse('pybb:add_post', args=[self.topic.id]), {'body': 'test closed'}, follow=True)
        #self.assertTrue(response.status_code==200)

    #def test_subscription(self):
        #user = User.objects.create_user(username='user2', password='user2', email='user2@example.com')
        #client = Client()
        #client.login(username='user2', password='user2')
        #response = client.get(reverse('pybb:add_subscription', args=[self.topic.id]), follow=True)
        #self.assertTrue(response.status_code==200)
        #self.assertTrue(user in list(self.topic.subscribers.all()))
        #new_post = Post(topic=self.topic, user=self.user, body='test subscribtion юникод', markup='bbcode')
        #new_post.save()
        #self.assertTrue([msg for msg in mail.outbox if new_post.get_absolute_url() in msg.body])
        #response = client.get(reverse('pybb:delete_subscription', args=[self.topic.id]), follow=True)
        #self.assertTrue(response.status_code==200)
        #self.assertTrue(user not in list(self.topic.subscribers.all()))

    #def test_topic_updated(self):
        #topic = Topic(name='etopic', forum=self.forum, user=self.user)
        #topic.save()
        #sleep(1)
        #post = Post(topic=topic, user=self.user, body='bbcode [b]test[b]', markup='bbcode')
        #post.save()
        #client = Client()
        #response = client.get(self.forum.get_absolute_url())
        #self.assertTrue(response.context['topic_list'][0]==topic)
        #sleep(1)
        #post = Post(topic=self.topic, user=self.user, body='bbcode [b]test[b]', markup='bbcode')
        #post.save()
        #client = Client()
        #response = client.get(self.forum.get_absolute_url())
        #self.assertTrue(response.context['topic_list'][0]==self.topic)


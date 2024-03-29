# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import Truncator
from django.utils.html import mark_safe
from markdown import markdown
import math


# Create your models here

class Country(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class User(AbstractUser):
    is_reporter = models.BooleanField(default=False)
    is_reader = models.BooleanField(default=False)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.username


class Subject(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return '{}--Name:{}'.format(self.id, self.name)


class Board(models.Model):
    name = models.CharField(max_length=30)
    subject = models.ForeignKey(Subject, related_name='boards', default=None,
                                on_delete=models.CASCADE)
    description = models.CharField(max_length=100)
    creater = models.ForeignKey(User, related_name='boards', default=None,
                                on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_posts_count(self):
        return Post.objects.filter(topic__board=self).count()

    def get_topics_count(self):
        return Topic.objects.filter(board=self).count()

    def get_last_post(self):
        return Post.objects.filter(topic__board=self).order_by('-created_at').first()


class Reader(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                primary_key=True)
    interests = models.ManyToManyField(Subject, default=None)

    def __str__(self):
        return self.user.username


class Topic(models.Model):
    subject = models.CharField(max_length=255)
    last_updated = models.DateTimeField(auto_now=True)
    board = models.ForeignKey(Board, related_name='topics',
                              on_delete=models.CASCADE)
    starter = models.ForeignKey(User, related_name='topics',
                                on_delete=models.CASCADE)
    views = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.subject

    def get_page_count(self):
        count = self.posts.count()
        pages = count / 20
        return math.ceil(pages) + 1

    def has_many_pages(self, count=None):
        if count is None:
            count = self.get_page_count()
        return count > 6

    def get_page_range(self):
        count = self.get_page_count()
        if self.has_many_pages(count):
            return range(1, 5)
        return range(1, int(count + 1))

    def get_last_ten_posts(self):
        return self.posts.order_by('-created_at')[:10]

    def get_all_posts(self):
        return self.posts.order_by('created_at')

    def get_replies(self):
        return self.posts.count()


class Post(models.Model):
    message = models.TextField(max_length=4000)
    topic = models.ForeignKey(Topic, related_name='posts',
                              on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, related_name='posts',
                                   on_delete=models.CASCADE)
    updated_by = models.ForeignKey(User, null=True, related_name='+',
                                   on_delete=models.CASCADE)

    def __str__(self):
        truncated_message = Truncator(self.message)
        return truncated_message.chars(30)

    def get_message_as_markdown(self):
        return mark_safe(markdown(self.message, safe_mode='escape'))


class Action(models.Model):
    EVENT_CHOICES = (
        ('add', 'create'),
        ('del', 'delete'),
        ('edt', 'edit'),
    )

    action = models.CharField(choices=EVENT_CHOICES, max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    board = models.ForeignKey(Board, null=True, related_name='actions',
                              on_delete=models.CASCADE)

    def __str__(self):
        return '{}-{}'.format(self.board.name, self.action)

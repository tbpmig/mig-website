import datetime
import factory
import string

from math import ceil, pow
from django.contrib.auth.models import User
from django.core.files import File
from django.utils.text import slugify

from about.models import AboutSlideShowPhoto, JoiningTextField

from mig_main.models import AcademicTerm
from mig_main.tests.factories import MemberProfileFactory,\
                                     OfficerPositionFactory

JOINING_TEXT = r'''A First Level Header
====================

A Second Level Header
---------------------

Now is the time for all good men to come to
the aid of their country. This is just a
regular paragraph.

The quick brown fox jumped over the lazy
dog's back.

### Header 3

> This is a blockquote.
>
> This is the second paragraph in the blockquote.
>
> ## This is an H2 in a blockquote'''

MARBLE_PATH = 'migweb/test_photos/about_marbles.jpg'


class AboutPhotoFactory(factory.DjangoModelFactory):
    class Meta:
        model = AboutSlideShowPhoto
    title = factory.Iterator(['Marbles', 'Flower'])
    text = factory.Iterator(['marbles', 'flower'])
    link = ''
    active = factory.Iterator([True, False])
    photo = factory.django.ImageField(from_path=MARBLE_PATH)


class JoiningTextFactory(factory.DjangoModelFactory):
    class Meta:
        model = JoiningTextField
    section = factory.Iterator(['EL', 'Y', 'UG', 'GR'])
    text = JOINING_TEXT

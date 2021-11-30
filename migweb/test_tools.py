from django.test.utils import setup_test_environment
from django.test import Client
from slimmer import html_slimmer

setup_test_environment()
MyClient = Client

def normalize_html(html):
  return html_slimmer(html).replace('\n', '').replace(' />', '/>').replace('> ', '>')

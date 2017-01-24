#!/usr/bin/env python

"""
Cron jobs
"""

import app_config
import json
import logging
import requests

from datetime import datetime
from fabric.api import local, require, task


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

today = datetime.now().strftime('%Y-%m-%d')
WEBHOOK = app_config.get_secrets()['WEBHOOK']
URL = 'https://www.federalregister.gov/api/v1/documents.json'

COLORS_DICT = {
    'Rule': '#5cb85c',
    'Proposed Rule': '#5bc0de',
    'Presidential Document': '#d9534f'
}

@task
def post_message():
    """
    Example cron task. Note we use "local" instead of "run"
    because this will run on the server.
    """
    documents = get_documents()
    r = requests.post(WEBHOOK, data=json.dumps(documents))
    logger.info(r.text)

def get_documents():
    document_attachments = []

    params = {
        'format': 'json',
        'order': 'relevance',
        'conditions[publication_date][is]': today,
        'conditions[type][]': ['RULE', 'PRORULE', 'PRESDOCU']
    }

    documents = requests.get(URL, params=params).json()
    for document in documents['results']:
        document_attachments.append(build_attachment(document))

    return {
        'text': 'The Federal Register published {0} documents today.'.format(documents['count']),
        'attachments': document_attachments
    }

def build_attachment(document):
    return {
        'fallback': document['title'],
        'color': COLORS_DICT[document['type']],
        'author_name': document['agencies'][0]['name'],
        'author_link': document['agencies'][0]['url'],
        'title': document['title'],
        'title_link': document['html_url'],
        'fields': [
            {
                'title': 'Type',
                'value': document['type']
            }
        ],
        'text': document.get('abstract', '')
    }

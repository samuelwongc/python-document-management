import json
import time

from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Document, LenderDocument, Lender


class DocumentTests(APITestCase):
    def createUser(self, username, permissions, lender):
        user = User.objects.create_user(username=username, password=username, email=username)
        user.user_permissions.set(permissions)
        user.profile.lender = lender
        user.save()
        return user

    def setUp(self):
        p_r = Permission.objects.get(codename='read_document')
        p_w = Permission.objects.get(codename='draft_document')
        p_x = Permission.objects.get(codename='publish_document')
        usernames = [
            ('u_none', []),
            ('u_r', [p_r]),
            ('u_rw', [p_r, p_w]),
            ('u_rwx', [p_r, p_w, p_x])
        ]
        self.lender = Lender.objects.create(name='test_lender_name')
        self.lender_document = LenderDocument.objects.create(lender=self.lender, name='test_lender_document')
        self.users = {
            u: self.createUser(u, p, self.lender) for u, p in usernames
        }
        Document.create(
            lender_document=self.lender_document,
            created_user=self.users['u_rwx'],
            content='TESTDOCUMENTCONTENT'
        )

    def test_retrieve_document(self):
        document = self.lender_document.documents.all()[0]
        url = reverse('document-detail', kwargs={'pk': document.document_id})
        self.client.force_authenticate(user=self.users['u_rwx'])
        response = self.client.get(url)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEquals(document.get_content(), response_json['content'])
        
    def test_list_document(self):
        url = reverse('document-list')
        self.client.force_authenticate(user=self.users['u_rwx'])
        response = self.client.get(url)
        documents = json.loads(response.content.decode('utf-8'))['results']
        self.assertEquals(len(documents), 1)
        self.assertEquals(documents[0]['version_minor'], 1)
        self.assertEquals(documents[0]['version_major'], 0)

    def test_draft_document(self):
        url = reverse('document-list')
        data = {
            'lender_document_id': self.lender_document.lender_document_id,
            'content': 'the quick brown fox jumps over the lazy dog'
        }
        self.client.force_authenticate(user=self.users['u_rwx'])
        response = self.client.post(url, data, format='json')
        new_document = self.lender_document.documents.order_by('-created_at')[0]
        url = reverse('document-detail', kwargs={'pk': new_document.document_id})
        response = self.client.get(url)
        document = json.loads(response.content.decode('utf-8'))
        self.assertEquals(document['content'], data['content'])

    def test_publish_document(self):
        previous_active_document = Document.create(
            lender_document=self.lender_document,
            created_user=self.users['u_rwx'],
            content='ACTIVE'
        )
        previous_active_document.publish()
        published_document_content = 'TESTDOCUMENTCONTENT TO BE PUBLISHED'
        published_document = Document.create(
            lender_document=self.lender_document,
            created_user=self.users['u_rwx'],
            content=published_document_content
        )
        url = reverse('document-publish', kwargs={'pk': published_document.document_id})
        self.client.force_authenticate(user=self.users['u_rwx'])
        response = self.client.post(url)

        # Sleep 3 seconds for S3 to replicate
        # From AWS S3 Developer Docs:
        #     However, information about the changes might not immediately replicate across 
        #     Amazon S3 and you might observe the following behaviors: A process writes a
        #     new object to Amazon S3 and immediately attempts to read it. Until the change
        #     is fully propagated, Amazon S3 might report "key does not exist."
        time.sleep(3)

        lender_document = LenderDocument.objects.get(lender_document_id=self.lender_document.lender_document_id)
        documents = lender_document.documents.order_by('-created_at')
        self.assertEquals(previous_active_document.version_major + 1, lender_document.active_document.version_major)
        self.assertEquals(0, lender_document.active_document.version_minor)
        self.assertEquals(published_document.document_id, lender_document.active_document.document_id)

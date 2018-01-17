import boto3
from datetime import datetime

from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models

from django.conf import settings
from django.utils import timezone

s3_client = boto3.client('s3')


class Lender(models.Model):
    lender_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    lender = models.ForeignKey(Lender, null=True, blank=True, related_name='users', on_delete=models.CASCADE)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_delete, sender=Profile)
def auto_delete_user(sender, instance, **kwargs):
    instance.user.delete()

class LenderDocument(models.Model):
    lender_document_id = models.AutoField(primary_key=True)
    lender = models.ForeignKey(Lender, related_name='document_types', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    active_document = models.ForeignKey('Document', null=True, blank=True, on_delete=models.SET_NULL)

class Document(models.Model):
    document_id = models.AutoField(primary_key=True)
    s3_bucket = models.CharField(max_length=50)
    s3_bucket_key = models.CharField(max_length=60)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, related_name='drafts', null=True, on_delete=models.SET_NULL)
    version_major = models.IntegerField()
    version_minor = models.IntegerField()
    lender_document = models.ForeignKey(LenderDocument, related_name='documents', on_delete=models.CASCADE)

    @classmethod
    def create(cls, lender_document, created_user, content):
        try:
            prev_document = lender_document.documents.order_by('-created_at')[0]
            version_major = prev_document.version_major
            version_minor = prev_document.version_minor + 1
        except: 
            version_major = 0
            version_minor = 1

        s3_bucket_key = '{}/{}-{}_{}_{}'.format(
            settings.ENV,
            lender_document.lender.lender_id,
            lender_document.name.replace(' ', '').lower(),
            version_major,
            version_minor
        )
        s3_client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=s3_bucket_key,
            Body=content.encode()
        )

        return cls.objects.create(
            s3_bucket=settings.S3_BUCKET,
            s3_bucket_key=s3_bucket_key,
            version_major=version_major,
            version_minor=version_minor,
            lender_document=lender_document,
            created_by=created_user
        )

    def get_content(self):
        return s3_client.get_object(
            Bucket=self.s3_bucket,
            Key=self.s3_bucket_key
        )['Body'].read().decode()
    
    def publish(self):
        if not self.lender_document.active_document:
            self.version_major = 1
            self.version_minor = 0
            self.created_at = timezone.now()
            self.save()
            lender_document = self.lender_document
            lender_document.active_document = self
            lender_document.version_number = 1
            lender_document.save()
            return
        if self.lender_document.active_document == self:
            return # Do nothing if active document being republished
        new_version_major = self.lender_document.active_document.version_major + 1
        self.version_major = new_version_major
        self.version_minor = 0
        self.created_at = timezone.now()
        self.save()
        self.lender_document.active_document = self
        self.lender_document.version_number = new_version_major
        self.lender_document.save()


    class Meta:
        permissions = (
            ("read_document", "Read documents"),
            ("draft_document", "Draft documents"),
            ("publish_document", "Publish documents"),
        )
from rest_framework import serializers

from .models import Document, LenderDocument


class DocumentSerializer(serializers.ModelSerializer):
    created_user = serializers.CharField(source='created_by.username')
    class Meta:
        model = Document
        fields = ('document_id', 'created_at', 'version_major', 'version_minor', 'created_user')
        read_only_fields = ('document_id',)


class LenderDocumentSerializer(serializers.ModelSerializer):
    active_version = serializers.IntegerField(default=-1, source='active_document.version_major')
    active_document_id = serializers.IntegerField(default=-1,source='active_document.document_id')
    class Meta:
        model = LenderDocument
        fields = ('lender_document_id', 'name', 'active_version', 'active_document_id')
        read_only_fields = ('lender_document_id', 'active_version', 'active_document_id')

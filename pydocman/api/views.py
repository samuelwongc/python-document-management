import boto3

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import mixins, viewsets
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated

from .models import Document, LenderDocument
from .permissions import DocumentModelPermission, DocumentModelPublishPermission, DocumentModelRevertPermission, LenderDocumentModelPermission
from .serializers import DocumentSerializer, LenderDocumentSerializer


s3 = boto3.client('s3')


class DocumentViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (DocumentModelPermission,)

    def list(self, request):
        documents = self.get_queryset().all()
        lender_document = self.request.query_params.get('type', None)
        if lender_document:
            documents = documents.filter(lender_document=lender_document)
        state = self.request.query_params.get('state', None)
        if state == 'published':
            documents = documents.filter(version_minor=0)

        documents = self.paginate_queryset(documents)
        serializer = DocumentSerializer(documents, many=True)
        return self.get_paginated_response(serializer.data)
        
    def create(self, request):
        try:
            lender_document_id = request.data['lender_document_id']
            lender_document = LenderDocument.objects.get(lender_document_id=lender_document_id)
            content = request.data['content']
        except:
            return JsonResponse({'error_msg': 'Invalid request.'}, status=400)
        document = Document.create(lender_document, request.user, content)
        serializer = DocumentSerializer(document, many=False)
        return JsonResponse(serializer.data, status=201, safe=False)

    def retrieve(self, request, pk=None):
        try:
            document = self.get_queryset().get(document_id=pk)
        except:
            return JsonResponse({'error_msg': 'Invalid request.'}, status=400)
        serializer = DocumentSerializer(document, many=False)
        data = serializer.data
        data['content'] = document.get_content()
        return JsonResponse(data, status=200, safe=False)

    @detail_route(permission_classes=[DocumentModelPublishPermission], methods=['post'])
    def publish(self, request, pk=None):
        try:
            document = self.get_queryset().get(document_id=pk)
        except:
            return JsonResponse({'error_msg': 'Invalid request.'}, status=400)
        document = document.publish()
        serializer = DocumentSerializer(document, many=False)
        data = serializer.data
        data['content'] = document.get_content()
        return JsonResponse(data, status=200, safe=False)
    
    @detail_route(permission_classes=[DocumentModelRevertPermission], methods=['post'])
    def revert(self, request, pk=None):
        try:
            document = self.get_queryset().get(document_id=pk)
        except:
            return JsonResponse({'error_msg': 'Invalid request.'}, status=400)
        reverted_document = document.revert(request.user)
        serializer = DocumentSerializer(reverted_document, many=False)
        data = serializer.data
        data['content'] = reverted_document.get_content()
        return JsonResponse(data, status=200, safe=False)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Document.objects.all()
        return Document.objects.filter(lender_document__lender=self.request.user.profile.lender)


class LenderDocumentViewSet(mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (LenderDocumentModelPermission,)

    def list(self, request):
        lender_documents = self.get_queryset().all()
        serializer = LenderDocumentSerializer(lender_documents, many=True)
        return JsonResponse(serializer.data, status=200, safe=False)

    def create(self, request):
        serializer = LenderDocumentSerializer(data=request.data, many=False)
        lender = request.user.profile.lender
        if serializer.is_valid():
            serializer.save(lender=lender, active_document=None)
            return JsonResponse(serializer.data, status=201, safe=False)
        return JsonResponse(serializer.errors, status=400)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return LenderDocument.objects.all()
        return LenderDocument.objects.filter(lender=self.request.user.profile.lender)


def test(request):
    return render(request, 'crypto.html')

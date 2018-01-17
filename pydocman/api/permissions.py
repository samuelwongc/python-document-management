from rest_framework import permissions


class DocumentModelPublishPermission(permissions.BasePermission):
    message = 'User does not have permission to publish documents.'

    def has_permission(self, request, view):
        return request.user.has_perm('api.publish_document')

class DocumentModelRevertPermission(permissions.BasePermission):
    message = 'User does not have permission to revert documents.'

    def has_permission(self, request, view):
        return request.user.has_perm('api.draft_document')

class DocumentModelPermission(permissions.DjangoModelPermissions):
    def __init__(self):
        self.perms_map['GET'] = ['api.read_document']
        self.perms_map['POST'] = ['api.draft_document']


class LenderDocumentModelPermission(permissions.DjangoModelPermissions):
    def __init__(self):
        self.perms_map['POST'] = ['api.create_lender_document']
#coding:utf-8
import functools
from django.http import Http403

from rest_framework import permissions
from rest_framework.status import status
from rest_framework.response import Response

def role_check(role='super'):
    def wrapper(method):
        @functools.wraps(method)
        def _wrapper(req, *args, **kwargs):
            if req.user.is_admin:
                return method(req, *args, **kwargs)
            if role == "admin":
                app_uuid = kwargs.get("app_uuid", None)
                roles = req.user.roles.filter(app__uuid=app_uuid)
                if roles:
                    if roles[0].staff == "1":
                        return method(req, *args, **kwargs)
            if req.path.startswith('/api/'):
                return Response({}, status=status.HTTP_403_FORBIDDEN)
            raise Http403
        return _wraper
    return wrapper


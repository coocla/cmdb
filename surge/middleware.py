#coding:utf-8
# Django 中间件, 用来统一处理用户认证和权限鉴定
import json
from django.core.cache import cache
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings

from surge.models import UserAccounts
from surge.common import utils

class AuthenticationMiddleware(object):
    def process_request(self, request):
        '''
        请求预处理
        '''
        request.get_argument = self.get_argument
        if "X-Auth-Token" in request.session:
            user = cache.get(utils.REDIS_USER_TOKEN % request.session["X-Auth-Token"])
            if user:
                request.user = user
            request.channel = "console"
        else:
            apikey = request.META.get("HTTP_APIKEY", None)
            if apikey:
                try:
                    request.user = UserAccounts.objects.get_user(apikey=apikey)
                    request.channel = "api"
                except UserAccounts.DoesNotExist:
                    pass

        if not hasattr(request, "user"):
            if request.path != "/login":
                resp = HttpResponseRedirect("/login?next=%s" % request.path)
                resp['Location'] = "/login"
                return resp
        else:
            if request.path == "/login":
                return HttpResponseRedirect(request.REQUEST.get("next", "/"))

    def get_argument(self, request, keyword=None, default=None):
        '''
        根据Content-Type的值,进行参数的获取方式
        :param keyword: 参数名
        :param default: 默认值
        '''
        if request.META.get("Content-Type", None) == "application/json":
            try:
                body = json.loads(request.body)
            except:
                raise ValueError("Not json format")
        else:
            body = request.REQUEST
        if keyword:
            return body.get(keyword, default)
        return body

    def process_response(self, request, response):
        return response

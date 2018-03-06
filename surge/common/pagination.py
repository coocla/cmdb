#coding:utf-8
from django.conf import settings as cfg
from rest_framework.pagination import PageNumberPagination

class PagePagination(PageNumberPagination):
    page_size = cfg.PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = cfg.MAX_PAGE_SIZE

class ZonePagination(PageNumberPagination):
    page_size = 84
    page_size_query_param = 'page_size'
    max_page_size = 420


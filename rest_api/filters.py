#coding:utf-8
import operator
from functools import reduce

from django.db import models
from django.utils import six

from rest_framework import filters
from rest_framework.settings import api_settings


class SearchFilter(filters.SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search_fields = getattr(view, 'search_fields', None)

        if not search_fields:
            return queryset

        orm_lookups = [self.construct_search(six.text_type(search_field))
                       for search_field in search_fields]

        expression = []
        for search_term in self.get_search_terms(request):
            or_queries = [models.Q(**{orm_lookup: search_term})
                          for orm_lookup in orm_lookups]
            expression += or_queries
        queryset = queryset.filter(reduce(operator.or_, expression)).distinct()
        return queryset

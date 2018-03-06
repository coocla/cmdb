#coding:utf-8
from rest_framework import serializers
from rest_framework.reverse import reverse

class HyperLinkField(serializers.HyperlinkedIdentityField):
    def __init__(self, *args, **kwargs):
        self.lookup_mapping = kwargs.pop("lookup_mapping", {})
        super(HyperLinkField, self).__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        url_kwargs = {}
        for url_field, _model in self.lookup_mapping.iteritems():
            if _model != "self":
                model_obj = getattr(obj, _model)
                if hasattr(model_obj, "id"):
                    _field = getattr(model_obj, "id")
                else:
                    _field = getattr(model_obj, 'uuid')
            else:
                if hasattr(obj, "id"):
                    _field = getattr(obj, "id")
                else:
                    _field = getattr(obj, 'uuid')
            url_kwargs[url_field] = _field
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    def get_object(self, view_name, view_args, view_kwargs):
        lookup_kwargs = {}
        for url_field, _model in self.lookup_mapping.iteritems():
            if _model == "self":
                _field = "uuid"
            else:
                _field = _model
            lookup_kwargs[_field] = view_kwargs[url_field]
        return self.get_queryset().get(**lookup_kwargs)

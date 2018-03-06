from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.urlpatterns import format_suffix_patterns
from django.contrib import admin
admin.autodiscover()

from surge import views as surge_view

urlpatterns = patterns('surge.views',
    url(r'^/?$', 'index', name="index"),
    url(r'^login/?$', 'login', name="login"),
    url(r'^logout/?$', 'logout', name="logout"),

    url(r'^organizer/create/?$', surge_view.OrganizerCreate.as_view(), name="organizer_create"),

    url(r'^users/create/?$', surge_view.UserCreate.as_view(), name="user_create"),
    url(r'^users/profile/?$', surge_view.UserProfile.as_view(), name="user_profile"),
    url(r'^users/restapikey/?$', surge_view.ResetAPIKey.as_view(), name="reset_apikey"),
    url(r'^users/change-password/?$', surge_view.ChangePassword.as_view(), name="change_password"),

    url(r'^thirdapps/(?P<app_uuid>[a-z0-9]+)/load/?$', surge_view.ThirdAppsLoad.as_view(), name="3papp_load"),
    url(r'^thirdapps/create/?$', surge_view.ThirdAppsCreate.as_view(), name="3papp_create"),
    url(r'^thirdapps/(?P<app_uuid>[a-z0-9]+)/update/?$', surge_view.ThirdAppsUpdate.as_view(), name="3papp_update"),

    url(r'^(?P<app_uuid>[a-z0-9]+)/roles/create/?$', surge_view.RoleCreate.as_view(), name="role_create"),
    url(r'^(?P<app_uuid>[a-z0-9]+)/roles/(?P<role_uuid>[a-z0-9]+)/update/?$', surge_view.RoleUpdate.as_view(), name="role_update"),

    url(r'^ops/', include('operation.urls')),
    url(r'^cmdb/', include('asset.urls')),
    url(r'^api/', include('rest_api.urls')),
    url(r'docs/', include('django.contrib.admindocs.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

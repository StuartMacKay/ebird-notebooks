from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

import debug_toolbar

urlpatterns = [
    # Change the path to the Django Admin to something non-standard.
    path("admin/", admin.site.urls),  # type: ignore
    path("__debug__/toolbar/", include(debug_toolbar.urls)),
] + staticfiles_urlpatterns()

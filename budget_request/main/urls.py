from django.contrib import admin
from django.urls import include, path

from main.views import permission_denied

urlpatterns = [
    path("", include("apps.admin_panel.urls")),
    path("", include("apps.budget.urls")),
    path("django-admin/", admin.site.urls),
]

handler403 = permission_denied

"""
URL configuration for agent_face_pro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from myapp import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url='/collect_page/', permanent=False)),
    path("collect_page/", views.return_collect_page),
    path("face_collect/", views.face_collect),
    path("detect_page/", views.return_detect_page),
    path("face_detect/", views.face_detect),
    path("login/",views.login),
    path("chat_stream/",views.chat_stream),
    path("chat_stream_llm/",views.chat_stream_llm),
    path("chat_agent/",views.chat_agent),
    path("chat_agent_page/",views.chat_agent_page),
    path("assistant_page/", views.assistant_page),
    path("schedule/add/", views.schedule_add),
    path("schedule/list/", views.schedule_list),
    path("schedule/delete/", views.schedule_delete),
    path("expense/add/", views.expense_add),
    path("expense/list/", views.expense_list),
    path("expense/delete/", views.expense_delete),
    path("translate/", views.translate_api),
    path("train_ticket/", views.train_ticket_search),
    path("flight_ticket/", views.flight_ticket_search),
    path("smart_qa/", views.smart_qa),
    path("data_analysis/db/", views.data_analysis_db),
    path("data_analysis/upload/", views.data_analysis_upload),
    path("data_analysis/file/", views.data_analysis_file),
    path("profile_page/", views.profile_page),
    path("change_password/", views.change_password),
]

# 开发环境下提供静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

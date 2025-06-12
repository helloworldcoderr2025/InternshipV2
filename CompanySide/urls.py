from django.urls import path
from .views import TNP_Dashboard_view, upload_company_details_view,upload_company_details_bulk_view
from .views import download_company_table_template_view,check_company_invite_status_view,fetching_company_invitation_status
from . import views


urlpatterns = [
    path('TNP_Dashboard',TNP_Dashboard_view,name="TNP_Dashboard"),
    path('upload_company_details',upload_company_details_view,name="upload_company_details"),
    path('upload_company_details_bulk',upload_company_details_bulk_view,name="upload_company_details_bulk"),
    path('download_company_table_template',download_company_table_template_view,name="download_company_table_template"),
    path('check_company_invite_status',check_company_invite_status_view,name="check_company_invite_status"),
    path('company-search/', views.company_search_page, name='company_search'),
    path('api/search/', views.search_companies),
    path('api/company/<str:company_id>/', views.get_company),
    path('api/company/<str:company_id>/update/', views.update_company),
    path('api/company/<str:company_id>/delete/', views.delete_company),
    path('fetching_company_invitation_status/', views.fetching_company_invitation_status_view,name="fetching_company_invitation_status"),
    path('get_email_preview/', views.get_email_preview_view,name="get_email_preview"),
    path('send_email/', views.send_email_view,name="send_email"),
]
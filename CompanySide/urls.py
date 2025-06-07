from django.urls import path
from .views import TNP_Dashboard_view, upload_company_details_view,upload_company_details_bulk_view
from .views import download_company_table_template_view,check_company_invite_status_view,fetching_company_invitation_status


urlpatterns = [
    path('TNP_Dashboard',TNP_Dashboard_view,name="TNP_Dashboard"),
    path('upload_company_details',upload_company_details_view,name="upload_company_details"),
    path('upload_company_details_bulk',upload_company_details_bulk_view,name="upload_company_details_bulk"),
    path('download_company_table_template',download_company_table_template_view,name="download_company_table_template"),
    path('check_company_invite_status',check_company_invite_status_view,name="check_company_invite_status"),
    path('fetching_company_invitation_status/',fetching_company_invitation_status,name="fetching_company_invitation_status"),
]
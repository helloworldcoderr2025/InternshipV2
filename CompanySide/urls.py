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
    path('api/search/', views.search_companies, name='search_companies'),
    path('api/company/<int:company_id>/', views.get_company, name='get_company'),
    path('api/company/<int:company_id>/update/', views.update_company, name='update_company'),
    path('api/company/<int:company_id>/delete/', views.delete_company, name='delete_company'),
    path('api/jobprofile/<int:profile_id>/update/', views.update_jobprofile, name='update_jobprofile'),
    path('api/jobprofile/<int:profile_id>/delete/', views.delete_jobprofile, name='delete_jobprofile'),
    path('fetching_company_invitation_status/', views.fetching_company_invitation_status_view,name="fetching_company_invitation_status"),
    path('get_email_preview/', views.get_email_preview_view,name="get_email_preview"),
    path('send_email/', views.send_email_view,name="send_email"),
    path('company-data-portal/', views.company_data_portal, name='company_data_portal'),
    path('invitations/', views.company_invitations_portal, name='company_invitations_portal'),
    path('jobprofiles_autocomplete/', views.jobprofiles_autocomplete, name='jobprofiles_autocomplete'),
    path('jobprofile_detail/', views.jobprofile_detail, name='jobprofile_detail'),
    path('jobprofile_update/', views.jobprofile_update, name='jobprofile_update'),
    path('update_invitation_response_inline/', views.update_invitation_response_inline, name='update_invitation_response_inline'),
    path('add_announcement/', views.add_announcement_view, name='add_announcement'),
]
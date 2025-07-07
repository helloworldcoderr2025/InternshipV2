import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.urls import reverse
from urllib.parse import urlencode
from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import csv, openpyxl, json
from MainInterface.models import Company, CompanyInvitations, CompanyJobprofiles
from .utils import send_custom_email
from .serializers import CompanySerializer,CompanyWithProfilesSerializer,CompanyJobprofileSerializer

def TNP_Dashboard_view(request):
    return render(request, 'T&P_Dashboard.html')


def upload_company_details_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        type_of_company = request.POST.get('type_of_company')
        eligible_core_branch = request.POST.get('eligible_core_branch')
        eligible_non_core_branch = request.POST.get('eligible_non_core_branch')
        job_profile = request.POST.get('job_profile')
        job_offer = request.POST.get('job_offer')
        max_package_offered = request.POST.get('max_package_offered')
        eligible_passouts = request.POST.get('eligible_passouts')
        hr_contact_email = request.POST.get('hr_contact_email')
        hr_contact_phno = request.POST.get('hr_contact_phno')
        hr_contact_alternate = request.POST.get('hr_contact_alternate')
        google_form_link = request.POST.get('google_form_link')
        brochure = request.FILES.get('brochure')

        brochure_path = ''
        if brochure:
            with open(f'media/brochures/{brochure.name}', 'wb+') as f:
                for chunk in brochure.chunks():
                    f.write(chunk)
            brochure_path = f'brochures/{brochure.name}'

        # Create or get the company
        company, created = Company.objects.get_or_create(name=name)

        # Add job profile
        CompanyJobprofiles.objects.create(
            company=company,
            type_of_company=type_of_company,
            eligible_core_branch=eligible_core_branch,
            eligible_non_core_branch=eligible_non_core_branch,
            job_profile=job_profile,
            job_offer=job_offer,
            max_package_offered=float(max_package_offered or 0),
            eligible_passouts=eligible_passouts,
            hr_contact_email=hr_contact_email,
            hr_contact_phno=hr_contact_phno,
            hr_contact_alternate=hr_contact_alternate,
            google_form_link=google_form_link,
            brochure_path=brochure_path
        )

        messages.success(request, "Company & Job Profile added successfully!")
        return redirect('company_search')
    return render(request, 'upload_company_details.html')


def upload_company_details_bulk_view(request):
    if request.method == 'POST':
        file = request.FILES['bulk_file']
        file_name = file.name.lower()

        if file_name.endswith('.csv'):
            data = csv.reader(file.read().decode('utf-8').splitlines())
            header = next(data)
            for row in data:
                try:
                    company_name = row[1]
                    company, created = Company.objects.get_or_create(name=company_name)
                    CompanyJobprofiles.objects.create(
                        company=company,
                        type_of_company=row[2],
                        eligible_core_branch=row[3],
                        eligible_non_core_branch=row[4],
                        job_profile=row[6],
                        job_offer=row[7],
                        max_package_offered=float(row[8] or 0),
                        eligible_passouts=row[9],
                        hr_contact_email=row[10],
                        google_form_link=row[11],
                        brochure_path=''
                    )
                except Exception as e:
                    messages.error(request, f"Error on row {row}: {e}")
        elif file_name.endswith(('.xlsx', '.xls')):
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            for row in sheet.iter_rows(min_row=2, values_only=True):
                try:
                    company_name = row[1]
                    company, created = Company.objects.get_or_create(name=company_name)
                    CompanyJobprofiles.objects.create(
                        company=company,
                        type_of_company=row[2],
                        eligible_core_branch=row[3],
                        eligible_non_core_branch=row[4],
                        job_profile=row[6],
                        job_offer=row[7],
                        max_package_offered=float(row[8] or 0),
                        eligible_passouts=row[9],
                        hr_contact_email=row[10],
                        google_form_link=row[11],
                        brochure_path=''
                    )
                except Exception as e:
                    messages.error(request, f"Error on row {row}: {e}")
        else:
            messages.error(request, "Unsupported file format.")

        return redirect('company_search')
    return render(request, 'upload_company_details_bulk.html')


def download_company_table_template_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="company_template.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'company_id', 'name', 'type_of_company', 'eligible_core_branch',
        'eligible_non_core_branch', 'type_of_job', 'job_profile', 'job_offer',
        'max_package_offered', 'eligible_passouts', 'hr_contact_details',
        'google_form_link'
    ])
    return response

def check_company_invite_status_view(request):
    companies = Company.objects.all().order_by('name')
    return render(request, 'Invitation_Status.html', {'companies': companies})

@csrf_exempt
def fetching_company_invitation_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        company_ids = data.get('company_ids', [])
        results = []
        for company_id in company_ids:
            try:
                company = Company.objects.get(id=company_id)
                invites = CompanyInvitations.objects.filter(company_id=company_id)
                for invite in invites:
                    results.append({
                        'company_id': company.id,
                        'name': company.name,
                        'invited': True,
                        'dates': [invite.invited_date],
                        'reminders': invite.no_of_reminders,
                        'response_status': invite.response,
                    })
                if not invites.exists():
                    results.append({
                        'company_id': company.id,
                        'name': company.name,
                        'invited': False,
                        'dates': [],
                        'reminders': 0,
                        'response_status': None,
                    })
            except Company.DoesNotExist:
                continue
        return JsonResponse({'results': results})


def company_search_page(request):
    companies = Company.objects.all().order_by('name')
    return render(request, 'company_search.html', {'companies': companies})


@api_view(['GET'])
def search_companies(request):
    query = request.GET.get('q', '')
    companies = Company.objects.filter(name__icontains=query)
    serializer = CompanySerializer(companies, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_company(request, company_id):
    """
    Return single company with nested job profiles
    """
    company = get_object_or_404(Company, id=company_id)
    serializer = CompanyWithProfilesSerializer(company)
    return Response(serializer.data)

@api_view(['PUT'])
def update_company(request, company_id):
    """
    Update fields in Company table itself.
    """
    company = get_object_or_404(Company, id=company_id)
    serializer = CompanySerializer(company, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_company(request, company_id):
    """
    Delete the company record.
    """
    company = get_object_or_404(Company, id=company_id)
    company.delete()
    return Response({"message": "Deleted successfully"}, status=status.HTTP_200_OK)

@api_view(['PUT'])
def update_jobprofile(request, profile_id):
    """
    Update fields in a specific job profile.
    """
    profile = get_object_or_404(CompanyJobprofiles, id=profile_id)
    serializer = CompanyJobprofileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_jobprofile(request, profile_id):
    """
    Delete a specific job profile.
    """
    profile = get_object_or_404(CompanyJobprofiles, id=profile_id)
    profile.delete()
    return Response({"message": "Deleted successfully"}, status=status.HTTP_200_OK)
@csrf_exempt
def fetching_company_invitation_status_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            company_ids = data.get('company_ids', [])
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        results = []

        for cid in company_ids:
            try:
                company = Company.objects.get(id=cid)
                invites = CompanyInvitations.objects.filter(company=company).order_by('-invited_date')

                if invites.exists():
                    latest_invite = invites.first()
                    reminders = latest_invite.no_of_reminders or 0

                    # Safely parse and reformat dates if possible
                    date_list = []
                    for inv in invites:
                        raw_date = inv.invited_date
                        try:
                            parsed_date = datetime.strptime(raw_date, '%Y-%m-%d')  # Adjust if your format is different
                            formatted = parsed_date.strftime('%Y-%m-%d')
                        except Exception:
                            formatted = raw_date  # fallback if not parsable
                        date_list.append(formatted)

                    results.append({
                        'company_id': cid,
                        'name': company.name,
                        'invited': True,
                        'dates': date_list,
                        'reminders': reminders,
                        'response_status': latest_invite.response,
                    })
                else:
                    results.append({
                        'company_id': cid,
                        'name': company.name,
                        'invited': False,
                        'dates': [],
                        'reminders': 0,
                        'response_status': None,
                    })
            except Company.DoesNotExist:
                results.append({
                    'company_id': cid,
                    'name': 'Unknown Company',
                    'invited': False,
                    'dates': [],
                    'reminders': 0,
                    'response_status': None,
                })

        return JsonResponse({'results': results})
    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def get_email_preview_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        company_id = data['company_id']
        mode = data['mode']

        company = Company.objects.get(company_id=company_id)

        context = {
            'company': company,
            'invitation_date': timezone.now().date()
        }

        template_name = f"emails/{mode}.txt"
        email_body = render_to_string(template_name, context)

        return JsonResponse({'email': email_body})

    return JsonResponse({'error': 'Invalid method'}, status=405)



@csrf_exempt
def send_email_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        company_id = data['company_id']
        mode = data['mode']
        email_body = data['email']
        invited_date = data.get('invited_date')  # Might be None for reminder

        company = Company.objects.get(company_id=company_id)

        if mode == 'invitation':
            if not invited_date:
                return JsonResponse({'error': 'Invitation date is required'}, status=400)

            # Create or update the invitation
            CompanyInvitations.objects.update_or_create(
                company=company,
                defaults={
                    'invited_date': invited_date,
                    'no_of_reminders': '0',
                    'response': 'Pending',
                    'job_profile':company.job_profile,
                    'job_offer':company.job_offer
                }
            )
            print("Arrived in invitation")
            # Send email
            send_custom_email(
                subject="TNP Invitation",
                to_email=company.company_email,
                body=email_body
            )
            return JsonResponse({'status': 'invitation_sent'})

        elif mode == 'reminder':
            try:
                invitation = CompanyInvitations.objects.get(company=company)
                current_reminders = int(invitation.no_of_reminders or '0')
                invitation.no_of_reminders = str(current_reminders + 1)
                invitation.save()

                send_custom_email(
                    subject="TNP Reminder",
                    to_email=company.company_email,
                    body=email_body
                )
                return JsonResponse({'status': 'reminder_sent'})
            except CompanyInvitations.DoesNotExist:
                return JsonResponse({'error': 'Invitation not found for reminder'}, status=400)

        else:
            return JsonResponse({'error': 'Invalid mode'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from urllib.parse import urlencode


RESPONSE_CHOICES = [
    'Willing to come to campus',
    'Not willing to come to campus',
    'Not responded',
]

def update_response_view(request):
    invitations = CompanyInvitations.objects.select_related('company').all()
    selected_invite = None

    # Handle GET request to select an invitation
    if request.method == 'GET' and 'invitation_key' in request.GET:
        try:
            company_id, invited_date, job_profile, job_offer = request.GET['invitation_key'].split('|')
            selected_invite = get_object_or_404(
                CompanyInvitations,
                company_id=company_id,
                invited_date=invited_date,
                job_profile=job_profile,
                job_offer=job_offer
            )
        except ValueError:
            selected_invite = None  # Invalid invitation key format

    # Handle POST request to update response
    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        invited_date = request.POST.get('invited_date')
        job_profile = request.POST.get('job_profile')
        job_offer = request.POST.get('job_offer')
        new_response = request.POST.get('new_response')

        invitation = get_object_or_404(
            CompanyInvitations,
            company_id=company_id,
            invited_date=invited_date,
            job_profile=job_profile,
            job_offer=job_offer
        )

        invitation.response = new_response
        invitation.save()

        # ✅ Use reverse + urlencode for proper redirect with query string
        url = reverse('update_response')
        query_string = urlencode({
            'invitation_key': f'{company_id}|{invited_date}|{job_profile}|{job_offer}'
        })
        return redirect(f'{url}?{query_string}')

    return render(request, 'update_response.html', {
        'invitations': invitations,
        'selected_invite': selected_invite,
        'response_choices': RESPONSE_CHOICES,
    })


def company_data_portal(request):
    filter_type = request.GET.getlist('type_of_company')
    filter_profile = request.GET.getlist('job_profile')
    filter_offer = request.GET.getlist('job_offer')
    filter_name = request.GET.getlist('company_name')
    sort_by = request.GET.get('sort_by', 'company__name')
    sort_order = request.GET.get('sort_order', 'asc')
    page_number = request.GET.get('page', 1)

    qs = CompanyJobprofiles.objects.select_related('company')

    if filter_name:
        qs = qs.filter(company__name__in=filter_name)
    if filter_type:
        qs = qs.filter(type_of_company__in=filter_type)
    if filter_profile:
        qs = qs.filter(job_profile__in=filter_profile)
    if filter_offer:
        qs = qs.filter(job_offer__in=filter_offer)

    sort_map = {
        'company__name': 'company__name',
        'type_of_company': 'type_of_company',
        'job_profile': 'job_profile',
        'job_offer': 'job_offer',
        'max_package_offered': 'max_package_offered',
    }
    sort_field = sort_map.get(sort_by, 'company__name')
    if sort_order == 'desc':
        sort_field = f'-{sort_field}'
    qs = qs.order_by(sort_field)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'company_data_portal.html', context)

def company_invitations_portal(request):
    invited_status = request.GET.get('invited_status', '')
    if invited_status not in ['invited', 'not_invited']:
        invited_status = 'invited'  # default

    page_number = request.GET.get('page', 1)
    sort_by = request.GET.get('sort_by', 'invited_date')

    filter_profile = request.GET.getlist('job_profile')
    filter_offer = request.GET.getlist('job_offer')
    filter_response = request.GET.getlist('response')
    filter_name = request.GET.getlist('company_name')
    filter_type = request.GET.getlist('type_of_company')
    filter_branch = request.GET.getlist('branch')

    invited_sort_mapping = {
        'company': 'company__name',
        'invited_date': 'invited_date',
        'response': 'response',
        'no_of_reminders': 'no_of_reminders',
    }

    not_invited_sort_mapping = {
        'company': 'name',
    }

    data = []
    branches = ['BIO', 'CHE', 'CIV', 'CSE', 'ECE', 'EEE', 'MECH', 'MME']

    if invited_status == 'invited':
        qs = CompanyInvitations.objects.select_related('company') \
            .prefetch_related('company__companyjobprofiles_set')

        if filter_profile:
            qs = qs.filter(company__companyjobprofiles__job_profile__in=filter_profile)
        if filter_offer:
            qs = qs.filter(company__companyjobprofiles__job_offer__in=filter_offer)
        if filter_response:
            qs = qs.filter(response__in=filter_response)
        if filter_name:
            qs = qs.filter(company__name__in=filter_name)
        if filter_type:
            qs = qs.filter(company__companyjobprofiles__type_of_company__in=filter_type)

        if filter_branch:
            # Filter separately for eligible_core_branch
            qs_core = qs.filter(company__companyjobprofiles__eligible_core_branch__iregex=r'(' + '|'.join(filter_branch) + ')')
            # Filter separately for eligible_non_core_branch
            qs_non_core = qs.filter(company__companyjobprofiles__eligible_non_core_branch__iregex=r'(' + '|'.join(filter_branch) + ')')
            # Combine both QuerySets with OR
            qs = (qs_core | qs_non_core).distinct()

        data = qs.order_by(invited_sort_mapping.get(sort_by, 'invited_date')).distinct()
        data_type = 'invited'

    elif invited_status == 'not_invited':
        invited_company_ids = CompanyInvitations.objects.values_list('company_id', flat=True)

        qs = Company.objects.exclude(id__in=invited_company_ids) \
            .prefetch_related('companyjobprofiles_set')

        if filter_name:
            qs = qs.filter(name__in=filter_name)
        if filter_type:
            qs = qs.filter(companyjobprofiles__type_of_company__in=filter_type)
        if filter_profile:
            qs = qs.filter(companyjobprofiles__job_profile__in=filter_profile)
        if filter_offer:
            qs = qs.filter(companyjobprofiles__job_offer__in=filter_offer)

        if filter_branch:
            qs_core = qs.filter(companyjobprofiles__eligible_core_branch__iregex=r'(' + '|'.join(filter_branch) + ')')
            qs_non_core = qs.filter(companyjobprofiles__eligible_non_core_branch__iregex=r'(' + '|'.join(filter_branch) + ')')
            qs = (qs_core | qs_non_core).distinct()

        data = qs.order_by(not_invited_sort_mapping.get(sort_by, 'name')).distinct()
        data_type = 'not_invited'

    paginator = Paginator(data, 10)
    page_obj = paginator.get_page(page_number)

    # Filters
    profiles = CompanyJobprofiles.objects.values_list('job_profile', flat=True).distinct()
    offers = CompanyJobprofiles.objects.values_list('job_offer', flat=True).distinct()
    responses = CompanyInvitations.objects.values_list('response', flat=True).distinct()
    company_names = Company.objects.values_list('name', flat=True).distinct()
    company_types = CompanyJobprofiles.objects.values_list('type_of_company', flat=True).distinct()

    return render(request, 'company_invitations_portal.html', {
        'page_obj': page_obj,
        'invited_status': invited_status,
        'data_type': data_type,
        'filter_profile': filter_profile,
        'filter_offer': filter_offer,
        'filter_response': filter_response,
        'filter_name': filter_name,
        'filter_type': filter_type,
        'filter_branch': filter_branch,
        'branches': branches,
        'sort_by': sort_by,
        'profiles': profiles,
        'offers': offers,
        'responses': responses,
        'company_names': company_names,
        'company_types': company_types,
    })







@csrf_exempt
def jobprofiles_autocomplete(request):
    company_id = request.GET.get('company_id')
    matches = CompanyJobprofiles.objects.filter(
        company_id=company_id
    ).values('key', 'job_profile')
    return JsonResponse({'profiles': list(matches)})


@csrf_exempt
def jobprofile_detail(request):
    prof = CompanyJobprofiles.objects.get(key=request.GET['id'])
    return JsonResponse({
        'job_profile': prof.job_profile,
        'job_offer': prof.job_offer,
        'hr_contact_email': prof.hr_contact_email,
        'hr_contact_phno': prof.hr_contact_phno,
        'hr_contact_alternate': prof.hr_contact_alternate,
    })



@csrf_exempt
def jobprofile_update(request):
    body = json.loads(request.body)
    prof = CompanyJobprofiles.objects.get(key=body['id'])

    prof.job_offer = body.get('job_offer', prof.job_offer)
    prof.hr_contact_email = body.get('hr_contact_email', prof.hr_contact_email)
    prof.hr_contact_phno = body.get('hr_contact_phno', prof.hr_contact_phno)
    prof.hr_contact_alternate = body.get('hr_contact_alternate', prof.hr_contact_alternate)

    prof.save()

    return JsonResponse({'status': 'ok'})

@csrf_exempt
def update_invitation_response_inline(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        company_id = data.get('company_id')
        new_response = data.get('new_response')

        try:
            invitation = CompanyInvitations.objects.get(company_id=company_id)
            invitation.response = new_response
            invitation.save()
            return JsonResponse({'status': 'ok'})
        except CompanyInvitations.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invitation not found'}, status=404)

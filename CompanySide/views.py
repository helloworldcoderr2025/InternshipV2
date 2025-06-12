from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse,JsonResponse
from MainInterface.models import Company,CompanyInvitations
from django.template.loader import render_to_string
from .utils import send_custom_email
from django.utils import timezone
import csv,openpyxl,json

def TNP_Dashboard_view(request):
    return render(request,'T&P_Dashboard.html')

def upload_company_details_view(request):
    if request.method == 'POST':
        company_id = request.POST['company_id']
        name = request.POST.get('name')
        type_of_company = request.POST.get('type_of_company')
        eligible_core_branch = request.POST.get('eligible_core_branch')
        eligible_non_core_branch = request.POST.get('eligible_non_core_branch')
        type_of_job = request.POST.get('type_of_job')
        job_profile = request.POST.get('job_profile')
        job_offer = request.POST.get('job_offer')
        max_package_offered = request.POST.get('max_package_offered')
        eligible_passouts = request.POST.get('eligible_passouts')
        hr_contact_details = request.POST.get('hr_contact_details')
        google_form_link = request.POST.get('google_form_link')
        brochure = request.FILES.get('brochure')
        brochure_path = ''
        if brochure:
            # Save uploaded file 
            with open(f'media/brochures/{brochure.name}', 'wb+') as f:
                for chunk in brochure.chunks():
                    f.write(chunk)
            brochure_path = f'brochures/{brochure.name}'

        # Inserting the data into dbase
        Company.objects.create(
            company_id=company_id,
            name=name,
            type_of_company=type_of_company,
            eligible_core_branch=eligible_core_branch,
            eligible_non_core_branch=eligible_non_core_branch,
            type_of_job=type_of_job,
            job_profile=job_profile,
            job_offer=job_offer,
            max_package_offered=max_package_offered,
            eligible_passouts=eligible_passouts,
            hr_contact_details=hr_contact_details,
            google_form_link=google_form_link,
            brochure_path=brochure_path
        )

        return redirect('company_search')  


def upload_company_details_bulk_view(request):
    if request.method == 'POST':
        file = request.FILES['bulk_file']
        file_name = file.name.lower()

        if file_name.endswith('.csv'):
            data = csv.reader(file.read().decode('utf-8').splitlines())
            header = next(data)  #header
            for row in data:
                try:
                    Company.objects.create(
                        company_id=row[0],
                        name=row[1],
                        type_of_company=row[2],
                        eligible_core_branch=row[3], 
                        eligible_non_core_branch=row[4], 
                        type_of_job=row[5],
                        job_profile=row[6],
                        job_offer=row[7],
                        max_package_offered=row[8],
                        eligible_passouts=row[9],
                        hr_contact_details=row[10],
                        google_form_link=row[11],
                        brochure_path=''  
                    )
                except Exception as e:
                    messages.error(request, f"Failed on row {row}: {e}")
        elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            for row in sheet.iter_rows(min_row=2, values_only=True):  # header skipped
                try:
                    Company.objects.create(
                        company_id=row[0],
                        name=row[1],
                        type_of_company=row[2],
                        eligible_core_branch=row[3], 
                        eligible_non_core_branch=row[4], 
                        type_of_job=row[5],
                        job_profile=row[6],
                        job_offer=row[7],
                        max_package_offered=row[8],
                        eligible_passouts=row[9],
                        hr_contact_details=row[10],
                        google_form_link=row[11],
                        brochure_path=''
                    )
                except Exception as e:
                    messages.error(request, f"Error on row {row}: {e}")
        else:
            messages.error(request, "Unsupported file format.")

        return redirect('company_search')



def download_company_table_template_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="company_template.csv"'
    writer = csv.writer(response)
    headers = [
        'company_id',
        'name',
        'type_of_company',
        'eligible_core_branch',
        'eligible_non_core_branch',
        'type_of_job',
        'job_profile',
        'job_offer',
        'max_package_offered',
        'eligible_passouts',
        'hr_contact_details',
        'google_form_link'
    ]
    writer.writerow(headers)
    return response

def check_company_invite_status_view(request):
    companies = Company.objects.all()
    return render(request, 'Invitation_Status.html', {'companies': companies})

@csrf_exempt
def fetching_company_invitation_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        company_ids = data.get('company_ids', [])
        results = []

        for company_id in company_ids:
            try:
                company = Company.objects.get(company_id=company_id)
                invites = CompanyInvitations.objects.filter(company_id=company_id)
                results.append({
                    'name': company.name,
                    'invited': invites.exists(),
                    'dates': [str(invite.invited_date) for invite in invites]
                })
            except Company.DoesNotExist:
                continue

        return JsonResponse({'results': results})



from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import CompanySerializer


def company_search_page(request):
    companies = Company.objects.all()
    return render(request, 'company_search.html', {'companies': companies})

@api_view(['GET'])
def search_companies(request):
    query = request.GET.get('q', '')
    companies = Company.objects.filter(name__icontains=query)
    serializer = CompanySerializer(companies, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_company(request, company_id):
    company = Company.objects.get(company_id=company_id)
    serializer = CompanySerializer(company)
    return Response(serializer.data)

@api_view(['PUT'])
def update_company(request, company_id):
    company = Company.objects.get(company_id=company_id)
    serializer = CompanySerializer(company, data=request.data,partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

@api_view(['DELETE'])
def delete_company(request, company_id):
    company = Company.objects.get(company_id=company_id)
    company.delete()
    return Response({"message": "Deleted successfully"})

@csrf_exempt
def fetching_company_invitation_status_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        company_ids = data.get('company_ids', [])
        results = []

        for cid in company_ids:
            try:
                company = Company.objects.get(company_id=cid)
                invites = CompanyInvitations.objects.filter(company_id=cid).order_by('-invited_date')
                if invites.exists():
                    latest_invite = invites.first()
                    reminders = latest_invite.no_of_reminders or "0"
                    results.append({
                        'company_id': cid,
                        'name': company.name,
                        'invited': True,
                        'dates': [inv.invited_date for inv in invites],
                        'reminders': reminders,
                        'response_status': latest_invite.response,
                    })
                else:
                    results.append({
                        'company_id': cid,
                        'name': company.name,
                        'invited': False,
                        'dates': [],
                        'reminders': "0",
                        'response_status': None,
                    })
            except Company.DoesNotExist:
                continue

        return JsonResponse({'results': results})
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
                company_id=company_id,
                defaults={
                    'invited_date': invited_date,
                    'no_of_reminders': '0',
                    'response': 'Pending'
                }
            )

            # Send email
            send_custom_email(
                subject="TNP Invitation",
                to_email=company.hr_contact_details,
                body=email_body
            )
            return JsonResponse({'status': 'invitation_sent'})

        elif mode == 'reminder':
            try:
                invitation = CompanyInvitations.objects.get(company_id=company_id)
                current_reminders = int(invitation.no_of_reminders or '0')
                invitation.no_of_reminders = str(current_reminders + 1)
                invitation.save()

                send_custom_email(
                    subject="TNP Reminder",
                    to_email=company.hr_contact_details,
                    body=email_body
                )
                return JsonResponse({'status': 'reminder_sent'})
            except CompanyInvitations.DoesNotExist:
                return JsonResponse({'error': 'Invitation not found for reminder'}, status=400)

        else:
            return JsonResponse({'error': 'Invalid mode'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

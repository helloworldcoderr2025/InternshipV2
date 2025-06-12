from django.core.mail import send_mail

def send_custom_email(subject, to_email, body):
    send_mail(
        subject,
        body,
        'temporaryu223@gmail.com', 
        [to_email],
        fail_silently=False,
    )

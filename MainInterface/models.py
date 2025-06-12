from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Company(models.Model):
    company_id = models.TextField(primary_key=True)  # The composite primary key (company_id, name, job_profile, job_offer) found, that is not supported. The first column is selected.
    name = models.TextField()
    type_of_company = models.TextField(blank=True, null=True)
    eligible_core_branch = models.TextField(blank=True, null=True)
    job_profile = models.TextField()
    job_offer = models.TextField()
    max_package_offered = models.TextField(blank=True, null=True)
    eligible_passouts = models.TextField(blank=True, null=True)
    hr_contact_details = models.TextField(blank=True, null=True)
    google_form_link = models.TextField(blank=True, null=True)
    brochure_path = models.TextField(blank=True, null=True)
    eligible_non_core_branch = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'company'
        unique_together = (('company_id', 'name', 'job_profile', 'job_offer'),)


class CompanyInvitations(models.Model):
    company_id = models.TextField(primary_key=True)  # The composite primary key (company_id, invited_date) found, that is not supported. The first column is selected.
    invited_date = models.TextField()
    no_of_reminders = models.TextField(blank=True, null=True)
    response = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'company_invitations'
        unique_together = (('company_id', 'invited_date'),)


class CseDepartment(models.Model):
    roll_no = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    branch = models.TextField(blank=True, null=True)
    registration = models.TextField(blank=True, null=True)
    gate_rank = models.IntegerField(db_column='gate rank', blank=True, null=True)  # Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'cse_department'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Documents(models.Model):
    rollno = models.BigAutoField(primary_key=True)
    results = models.TextField()
    scorecard = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'documents'


class Mails(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    roll_no = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mails'


class MmeDepartment(models.Model):
    roll_no = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    branch = models.TextField(blank=True, null=True)
    registration = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mme_department'


class Placements(models.Model):
    name = models.TextField(blank=True, null=True)
    type_of_company = models.TextField(blank=True, null=True)
    eligible_branches = models.TextField(blank=True, null=True)
    type_of_job = models.TextField(blank=True, null=True)
    job_profile = models.TextField(blank=True, null=True)
    job_offer = models.TextField(blank=True, null=True)
    package = models.TextField(blank=True, null=True)
    year = models.TextField(blank=True, null=True)
    rollno = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'placements'


class Registrations(models.Model):
    registered_id = models.TextField(primary_key=True)
    rollnumber = models.TextField(blank=True, null=True)
    company_id = models.TextField(blank=True, null=True)
    level = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'registrations'


class Student(models.Model):
    roll_no = models.TextField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    branch = models.TextField(blank=True, null=True)
    registered = models.TextField(blank=True, null=True)
    job_type = models.TextField(blank=True, null=True)
    academic_year = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    gate_rank = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    mobile = models.TextField(blank=True, null=True)
    cgpa = models.TextField(blank=True, null=True)
    placed = models.TextField(blank=True, null=True)
    backlogs = models.TextField(blank=True, null=True)
    linkedin = models.TextField(blank=True, null=True)
    verified = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    profilepic = models.TextField(db_column='profilePic', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'student'
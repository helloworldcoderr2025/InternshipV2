# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
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
    registered_id = models.TextField(blank=True,primary_key=True)
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
    updated_at = models.DateTimeField(auto_now=True)
    profilepic = models.TextField(db_column='profilePic', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'student'


class Company(models.Model):
    company_id = models.TextField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    type_of_company = models.TextField(blank=True, null=True)
    eligible_core_branch = models.TextField(blank=True, null=True)
    type_of_job = models.TextField(blank=True, null=True)
    job_profile = models.TextField(blank=True, null=True)
    job_offer = models.TextField(blank=True, null=True)
    max_package_offered = models.TextField(blank=True, null=True)
    eligible_passouts = models.TextField(blank=True, null=True)
    hr_contact_details = models.TextField(blank=True, null=True)
    google_form_link = models.TextField(blank=True, null=True)
    brochure_path = models.TextField(blank=True, null=True)
    eligible_non_core_branch = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'company'


class Mails(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    roll_no = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mails'

class Documents(models.Model):
    rollno = models.BigAutoField(primary_key=True)
    results = models.TextField()
    scorecard = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'documents'

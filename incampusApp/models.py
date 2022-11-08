from django.db import models
from django.core import validators
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.
class StudentModel(models.Model):
    id = models.AutoField(primary_key=True)
    u_id = models.CharField(max_length=20, unique=True, db_column='u_id')
    u_name = models.CharField(max_length=100, db_column='name')
    password = models.CharField(max_length=4096, db_column='password')
    t_id = models.CharField(max_length=15, db_column='t_id')
    email = models.EmailField(null=True, db_column='email')
    major = models.CharField(max_length=100, db_column='major')
    createdAt = models.DateTimeField(db_column='createdAt')
    updatedAt = models.DateTimeField(db_column='updatedAt')

    class Meta:
        db_table = 'student'
    
class TeacherModel(models.Model):
    id = models.AutoField(primary_key=True)
    t_id = models.CharField(max_length=20, unique=True, db_column='t_id')
    t_name = models.CharField(max_length=100, db_column='name')
    password = models.CharField(max_length=4096, db_column='password')
    email = models.EmailField(null=True, db_column='email')
    createdAt = models.DateTimeField(db_column='createdAt')
    updatedAt = models.DateTimeField(db_column='updatedAt')

    class Meta:
        db_table = 'teacher'

class RecordModel(models.Model):
    id = models.AutoField(primary_key=True)
    u_id = models.CharField(max_length=20, db_column='u_id')
    ipaddr=models.CharField(max_length=50, null=True, db_column='ipaddr')
    memo = models.TextField(null=True, db_column='memo')
    comment = models.TextField(null=True, db_column='comment')
    createdAt = models.DateTimeField(null=True, db_column='createdAt')
    updatedAt = models.DateTimeField(null=True, db_column='updatedAt')
    s_notice = models.BooleanField(default=False)
    t_notice = models.BooleanField(default=False)

    class Meta:
        db_table='records'

class LaboratoryModel(models.Model):
    id = models.AutoField(primary_key=True)
    t_id = models.CharField(max_length=20, unique=True, db_column='t_id')
    lab_name = models.CharField(max_length=100, db_column='lab_name')
    s_core_time_start = models.TimeField(
        null=True,
        db_column='s_core_time_start'
    )
    s_core_time_end = models.TimeField(
        null=True,
        db_column='s_core_time_end'
    )
    m_core_time_start = models.TimeField(
        null=True,
        db_column='m_core_time_start'
    )
    m_core_time_end = models.TimeField(
        null=True,
        db_column='m_core_time_end'
    )
    d_core_time_start = models.TimeField(
        null=True,
        db_column='d_core_time_start'
    )
    d_core_time_end = models.TimeField(
        null=True,
        db_column='d_core_time_end'
    )
    createdAt = models.DateTimeField(db_column='createdAt')
    updatedAt = models.DateTimeField(db_column='updatedAt')

    class Meta:
        db_table = 'laboratory'
    

class MajorModel(models.Model):
    id = models.AutoField(primary_key=True)
    m_id = models.CharField(max_length=5, db_column='m_id')
    m_name = models.CharField(max_length=50, db_column='m_name')
    first_half_term = models.IntegerField(
        null=True,
        db_column='first_half_term',
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(10000)
        ]
    )
    second_half_term = models.IntegerField(
        null=True,
        db_column='second_half_term',
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(10000)
        ]
    )
    total_term = models.IntegerField(
        null=True,
        db_column='total_term',
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(10000)
        ]
    )
    createdAt = models.DateTimeField(db_column='createdAt')
    updatedAt = models.DateTimeField(db_column='updatedAt')

    class Meta:
        db_table = 'major'

class AdminModel(models.Model):
    id = models.AutoField(primary_key=True)
    admin_id = models.CharField(max_length=20, unique=True, db_column='admin_id')
    password = models.CharField(max_length=4096, db_column='password')
    createdAt = models.DateTimeField(db_column='createdAt')
    updatedAt = models.DateTimeField(db_column='updatedAt')
    class Meta:
        db_table = 'admin'

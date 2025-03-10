import os
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import connection
from django.core.mail import send_mail, EmailMessage
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login
from django.views.decorators.cache import never_cache
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from FitSculpt import settings
from .forms import *
from .models import *
from .tokens import custom_token_generator
from .decorators import *
from django.utils.html import strip_tags
from datetime import datetime,date
from django.core.files.storage import FileSystemStorage
from .utils.video_analyzer import WorkoutAnalyzer
from .utils.fitness_chatbot import FitnessChatbot
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import timedelta
from django.template.defaulttags import register
from django.utils.crypto import get_random_string
from .utils.delivery_utils import get_nearest_center, calculate_distance, get_pincode_coordinates
import random
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt  # Only for testing
from .utils.image_validator import ImageValidator
import time
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import pandas as pd

def dictfetchall(cursor):
    """Return all rows from a cursor as a list of dictionaries"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def index_view(request):
    return render(request, 'index.html')

def calculate_age(dob):
    today = datetime.today().date()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age
def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email address')
            return render(request, 'register.html')
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')
        if username in ['fm001', 'admin001']:
            messages.error(request, 'This username cannot be taken.')
            return render(request, 'register.html')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM client WHERE username = %s", [username])
                if cursor.fetchone()[0] > 0:
                    messages.error(request, 'Username already exists')
                    return render(request, 'register.html')
                cursor.execute("SELECT COUNT(*) FROM client WHERE email = %s", [email])
                if cursor.fetchone()[0] > 0:
                    messages.error(request, 'Email already registered')
                    return render(request, 'register.html')
                cursor.execute("SELECT COUNT(*) FROM client WHERE phone = %s", [phone])
                if cursor.fetchone()[0] > 0:
                    messages.error(request, 'Phone number already registered')
                    return render(request, 'register.html')
        except Exception as e:
            messages.error(request, f'Error checking username, email, or phone: {e}')
            return render(request, 'register.html')
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            if dob_date > datetime.today().date():
                messages.error(request, 'Date of birth cannot be in the future.')
                return render(request, 'register.html')
            age = calculate_age(dob_date)
        except ValueError:
            messages.error(request, 'Invalid date format. Use YYYY-MM-DD.')
            return render(request, 'register.html')
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO client (name, email, phone, dob, username, password, age, date_joined) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
                    [name, email, phone, dob_date, username, password, age]
                )
            messages.success(request, 'Account created successfully')
            return redirect('login')  
        except Exception as e:
            messages.error(request, f'Error occurred: {e}')
            return render(request, 'register.html')
    return render(request, 'register.html')


from django.utils import timezone
from datetime import timedelta

def update_inactive_payments(user_id):
    now = timezone.now()

    threshold_date = now - timedelta(days=30)

    Payment.objects.filter(user_id=user_id, active=1, payment_date__lt=threshold_date).update(active=0)



from django.utils import timezone
from datetime import timedelta
from .models import MentalFitness 

def update_expired_mental_classes(user_id):
    now = timezone.now()
    print(now) 

    threshold_time = now - timedelta(hours=1)

    updated_counts = MentalFitness.objects.filter(client_id=user_id,class_time__lt=threshold_time, status=1).update(status=0)

    return updated_counts  

from django.utils import timezone
from datetime import timedelta
from .models import MentalFitness 

def fm_update_expired_mental_classes(user_id):
    now = timezone.now() 

    threshold_time = now - timedelta(hours=1)

    updated_counts = MentalFitness.objects.filter(fm_id=user_id,class_time__lt=threshold_time, status=1).update(status=0)

    return updated_counts 

from django.utils import timezone
from datetime import timedelta
from .models import ClientFM 

def update_expired_classes(user_id):
    now = timezone.now() 

    threshold_time = now - timedelta(hours=1)

    updated_count = ClientFM.objects.filter(client_id=user_id,class_time__lt=threshold_time, status=1).update(status=0)

    return updated_count  

from django.utils import timezone
from datetime import timedelta
from .models import ClientFM 

def fm_update_expired_classes(user_id):
    now = timezone.now() 

    threshold_time = now - timedelta(hours=1)

    updated_count = ClientFM.objects.filter(fm_id=user_id,class_time__lt=threshold_time, status=1).update(status=0)

    return updated_count  


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = Client.objects.get(username=username)
            if user.status == 1:
                if user.password == password:  
                    request.session['user_id'] = user.user_id 
                    request.session['username'] = user.username  
                    print(user.age)
                    update_inactive_payments(user.user_id)
                    update_expired_classes(user.user_id)
                    update_expired_mental_classes(user.user_id)
                    return redirect('user_profile')  
                else:
                    messages.error(request, 'Invalid username or password.')
        except Client.DoesNotExist:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')



def google_login_view(request):
    return render(request, 'google_login.html')


def forgot_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')

        try:
            user = Client.objects.get(username=username, email=email)
            current_site = get_current_site(request)
            token = custom_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.user_id))

            reset_link = f"http://localhost:8000/reset/{uid}/{token}/"

            subject = 'Password Reset Request'
            html_message = render_to_string('reset_email.html', {
                'user': user,
                'reset_link': reset_link,
            })
            plain_message = strip_tags(html_message)

            email = EmailMessage(
                subject,
                html_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            email.content_subtype = 'html'
            email.send(fail_silently=False)

            messages.success(request, 'A reset link has been sent to your email.')
            return redirect('login')

        except Client.DoesNotExist:
            messages.error(request, 'Invalid username or email.')
            return render(request,'forgot.html')
    return render(request, 'forgot.html')


def reset_password_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Client.objects.get(user_id=uid)
    except (TypeError, ValueError, OverflowError, Client.DoesNotExist):
        user = None

    if user and custom_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(request.POST, user=user)
            if form.is_valid():
                new_password = form.cleaned_data.get('new_password')
                user.password = new_password 
                user.save()

                send_mail(
                    'Password Reset Successful',
                    f'Hello {user.username}, your password in FITSCULPT has been successfully reset.Thank You',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                messages.success(request, 'Your password has been reset successfully.')
                return redirect('login')
        else:
            form = SetPasswordForm(user=user)
        return render(request, 'reset_password.html', {'form': form, 'valid_link': True})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('forgot')


@fm_custom_login_required
def fm_home_view(request):
    return render(request, 'fm_home.html')

@fm_custom_login_required
def fm_home_view2(request):
    return render(request, 'fm_home2.html')

@fm_custom_login_required
def fm_home_view3(request):
    return render(request, 'fm_home3.html')

from django.shortcuts import render
from django.db import connection

@fm_custom_login_required
def fm_users(request):
    fm_id = request.session.get('fm_user_id')  # Assuming the logged-in user has an `fm_id`

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.user_id, c.name, c.email, c.phone, c.dob, c.username, c.gender, c.age, c.height, c.weight, c.date_joined
            FROM client c
            LEFT JOIN tbl_client_fm cf ON c.user_id = cf.client_id AND cf.fm_id = %s
            LEFT JOIN tbl_clientfm2 cf2 ON c.user_id = cf2.client_id AND cf2.fm_id = %s
            LEFT JOIN tbl_mental_fitness mf ON c.user_id = mf.client_id AND mf.fm_id = %s
            WHERE c.status = 1
            AND (cf.fm_id IS NOT NULL OR cf2.fm_id IS NOT NULL OR mf.fm_id IS NOT NULL)
        """, [fm_id, fm_id, fm_id])
        
        clients = cursor.fetchall()
        clients = [
            {
                'user_id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3],
                'dob': row[4],
                'username': row[5],
                'gender': row[6],
                'age': row[7],
                'height': row[8],
                'weight': row[9],
                'date_joined': row[10],
            }
            for row in clients
        ]

    context = {
        'clients': clients,
    }
    return render(request, 'fm_users.html', context)


from django.shortcuts import render
from django.db import connection

@fm_custom_login_required
def fm_payment(request):
    fm_id = request.session.get('fm_user_id')  # Get the fitness manager user ID from the session

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.payment_id, p.plan_id, pl.plan_name, pl.amount, p.user_id, c.name, p.payment_date, p.mode, p.status 
            FROM tbl_payment p
            JOIN client c ON p.user_id = c.user_id
            JOIN tbl_plans pl ON p.plan_id = pl.plan_id
            WHERE p.active = 1 AND (
                EXISTS (SELECT 1 FROM tbl_client_fm cf WHERE cf.client_id = p.user_id AND cf.fm_id = %s) OR
                EXISTS (SELECT 1 FROM tbl_clientfm2 cf2 WHERE cf2.client_id = p.user_id AND cf2.fm_id = %s) OR
                EXISTS (SELECT 1 FROM tbl_mental_fitness mf WHERE mf.client_id = p.user_id AND mf.fm_id = %s)
            )
        """, [fm_id, fm_id, fm_id])

        payments = cursor.fetchall()
        payments = [
            {
                'payment_id': row[0],
                'plan_id': row[1],
                'plan_name': row[2],
                'amount': row[3],
                'user_id': row[4],
                'name': row[5],
                'payment_date': row[6],
                'mode': row[7],
                'status': row[8],
            } 
            for row in payments
        ]

    context = {
        'payments': payments,
    }
    return render(request, 'fm_payment.html', context)




@admin_custom_login_required
def admin_payment(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.payment_id, p.plan_id, pl.plan_name,pl.amount,p.user_id,c.name, p.payment_date, p.mode, p.status 
            FROM tbl_payment p
            JOIN client c ON p.user_id = c.user_id
            JOIN tbl_plans pl ON p.plan_id = pl.plan_id
        """)
        payments = cursor.fetchall()
        payments = [
            {
                'payment_id': row[0],
                'plan_id': row[1],
                'plan_name': row[2],
                'amount': row[3],
                'user_id': row[4],
                'name': row[5],
                'payment_date': row[6],
                'mode': row[7],
                'status': row[8],
                  
                
            } 
            for row in payments
        ]

        cursor.execute("""
            SELECT p.payment_id, p.plan_id, pl.plan_name,pl.amount,p.user_id,c.name, p.payment_date, p.mode, p.status 
            FROM tbl_payment p
            JOIN client c ON p.user_id = c.user_id
            JOIN tbl_plans pl ON p.plan_id = pl.plan_id
            WHERE p.active = 1 """)
        active_payments = cursor.fetchall()
        active_payments = [
            {
                'payment_id': row[0],
                'plan_id': row[1],
                'plan_name': row[2],
                'amount': row[3],
                'user_id': row[4],
                'name': row[5],
                'payment_date': row[6],
                'mode': row[7],
                'status': row[8],
            } 
            for row in active_payments
        ]
        context = {
        'payments': payments,
        'active_payments': active_payments
    }
    return render(request, 'admin_payment.html',context)

@fm_custom_login_required
def fm_profile_view(request):
    user_id = request.session.get('fm_user_id')
    if user_id:
        tbl_fitness_manager = FitnessManager.objects.get(user_id=user_id)
        
        if request.method == 'POST':
            form = FmUpdateForm(request.POST, instance=tbl_fitness_manager)
            if form.is_valid():
                form.save()
                return redirect('fm_profile')
            else:
                return render(request, 'fm_profile.html', {'form': form, 'tbl_fitness_manager': tbl_fitness_manager})
        else:
            form = FmUpdateForm(instance=tbl_fitness_manager)
        
        return render(request, 'fm_profile.html', {'form': form, 'tbl_fitness_manager': tbl_fitness_manager})
    
    return redirect('fm_login')


@fm_custom_login_required
def fm_logout_view(request):
    request.session.flush()
    return redirect('fm_login')


import datetime   
from  django.core.files.storage import FileSystemStorage
def fm_register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        email = request.POST.get('email').strip()
        phone = request.POST.get('phone').strip()
        qualification = request.POST.get('qualification')
        designation = request.POST.get('designation')
        certificate=request.FILES.get('certificate_proof',None)
        certificate_url=None
        if certificate:
            fs= FileSystemStorage()
            filename=fs.save(certificate.name,certificate)
            certificate_url=fs.url(filename)
        else:
            messages.error(request,'Please Upload Your certificate proof.')
            return render(request,'fm_register.html')
        try:
            with connection.cursor() as cursor:
                
                cursor.execute("SELECT COUNT(*) FROM tbl_fitness_manager WHERE email = %s", [email])
                if cursor.fetchone()[0] > 0:
                    messages.error(request, 'Email already registered')
                    return render(request, 'fm_register.html')

                cursor.execute("SELECT COUNT(*) FROM tbl_fitness_manager WHERE phone = %s", [phone])
                if cursor.fetchone()[0] > 0:
                    messages.error(request, 'Phone number already registered')
                    return render(request, 'fm_register.html')

                # Get qualification_id from the database
                cursor.execute("SELECT qualification_id FROM tbl_qualifications WHERE qualification = %s", [qualification])
                qualification_id = cursor.fetchone()
                if not qualification_id:
                    messages.error(request, 'Invalid qualification selected')
                    return render(request, 'fm_register.html')
                qualification_id = qualification_id[0]

                # Get designation_id from the database
                cursor.execute("SELECT designation_id FROM tbl_designations WHERE designation = %s", [designation])
                designation_id = cursor.fetchone()
                if not designation_id:
                    messages.error(request, 'Invalid designation selected')
                    return render(request, 'fm_register.html')
                designation_id = designation_id[0]

                # Insert into tbl_fitness_manager
                date_joined = datetime.now()
                cursor.execute("""
                    INSERT INTO tbl_fitness_manager (name, email, phone, qualification_id, designation_id,certificate_proof, date_joined)
                    VALUES (%s, %s, %s, %s, %s, %s,%s)
                """, [name, email, phone, qualification_id, designation_id,filename, date_joined])
                messages.success(request, 'You have requested for job successfully')
                messages.success(request, 'You Will get a mail from FITSCULPT regarding your Application Status...')

                return redirect('fm_register')

        except Exception as e:
            messages.error(request, f'Error processing your request: {e}')
            return render(request, 'fm_register.html')

    return render(request, 'fm_register.html')

def fm_forgot_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')

        try:
            user = FitnessManager.objects.get(username=username, email=email)
            current_site = get_current_site(request)
            token = custom_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.user_id))

            reset_link = f"http://localhost:8000/fm_reset/{uid}/{token}/"

            subject = 'Password Reset Request'
            html_message = render_to_string('fm_reset_email.html', {
                'user': user,
                'reset_link': reset_link,
            })
            plain_message = strip_tags(html_message)

            email = EmailMessage(
                subject,
                html_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            email.content_subtype = 'html'
            email.send(fail_silently=False)

            messages.success(request, 'A reset link has been sent to your email.')
            return redirect('fm_login')

        except FitnessManager.DoesNotExist:
            messages.error(request, 'Invalid username or email.')

    return render(request, 'fm_forgot.html')

def fm_reset_password_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        print(f"Decoded UID: {uid}")
        user = FitnessManager.objects.get(user_id=uid)
        print(f"Retrieved User: {user}")
    except (TypeError, ValueError, OverflowError, FitnessManager.DoesNotExist):
        user = None
        print("User retrieval failed")

    if user and custom_token_generator.check_token(user, token):
        print("Token is valid")
        if request.method == 'POST':
            form = Fm_SetPasswordForm(request.POST, user=user)
            if form.is_valid():
                print("Form is valid")
                new_password = form.cleaned_data.get('new_password')
                user.password = new_password 
                user.save()
                print("Password updated successfully")

                send_mail(
                    'Password Reset Successful',
                    f'Hello {user.username}, your password in FITSCULPT has been successfully reset.Thank You',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                messages.success(request, 'Your password has been reset successfully.')
                return redirect('fm_login')
            else:
                print("Form is not valid")
                print(form.errors)
        else:
            form = Fm_SetPasswordForm(user=user)
        return render(request, 'fm_reset_password.html', {'form': form, 'valid_link': True})
    else:
        print("Token is invalid or link has expired")
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('fm_forgot')



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import FitnessManager

def fm_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = FitnessManager.objects.get(username=username)
            if user.status == 1: 
                if user.password == password:  
                    request.session['fm_user_id'] = user.user_id 
                    request.session['username'] = user.username 
                    fm_update_expired_classes(user.user_id)
                    fm_update_expired_mental_classes(user.user_id) 
                    return redirect('fm_home')  
                
                else:
                    messages.error(request, 'Invalid username or password.')
        except FitnessManager.DoesNotExist:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'fm_login.html')

from django.utils import timezone
from datetime import timedelta

def update_inactive_payments(user_id):
    now = timezone.now()

    threshold_date = now - timedelta(days=30)

    Payment.objects.filter(user_id=user_id, active=1, payment_date__lt=threshold_date).update(active=0)


@custom_login_required
def user_home_view(request):
    return render(request, 'user_home.html')
@custom_login_required
def user_profile_view(request):
    user_id = request.session.get('user_id')  

    if user_id:
        client = Client.objects.get(user_id=user_id)  

        if request.method == 'POST':
            form = ClientUpdateForm(request.POST,request.FILES, instance=client)
            
            new_username = request.POST.get('username')
            
            if Client.objects.filter(username=new_username).exclude(user_id=user_id).exists():
                form.add_error('username', "This username is already taken.")
            
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile Updated successfully')
                return redirect('user_profile')
        else:
            form = ClientUpdateForm(instance=client)
        
        bmi = None
        if client.height and client.weight:  
            height_in_meters = client.height / 100  
            bmi = client.weight / (height_in_meters ** 2)

        return render(request, 'user_profile.html', {'form': form, 'client': client, 'bmi': bmi})
    
    return redirect('login')


@custom_login_required
def logout_view(request):
    request.session.flush()
    return redirect('login')


from django.shortcuts import render
from .models import Plan, Client  

@custom_login_required
def plans_view(request):
    plans = Plan.objects.all()  
    plan_id = request.POST.get('plan_id')
    user_id = request.session.get('user_id')
    previous_plan_amount = request.session.get('previous_plan_amount', None)
 
    print(user_id, plan_id)
    
    user_age = None
    if user_id:
        try:
            client = Client.objects.get(user_id=user_id)
            user_age = client.age 
        except Client.DoesNotExist:
            user_age = None

    is_child_plan_enabled = user_age is not None and user_age < 12

    # Check if the user has an active plan (active=1)
    user_has_plan = Payment.objects.filter(user_id=user_id, active=1).exists()

    current_plan = None
    current_plan_name = None
    if user_has_plan:
        payment_record = Payment.objects.filter(user_id=user_id, active=1).first()
        if payment_record:
            current_plan = payment_record.plan_id

            # Get the current plan name
            plan_record = Plan.objects.filter(plan_id=current_plan).first()
            if plan_record:
                current_plan_name = plan_record.plan_name
    
    print(current_plan)
    print(current_plan_name)
    
    return render(request, 'plans.html', {
        'plans': plans,
        'is_child_plan_enabled': is_child_plan_enabled,
        'user_has_plan': user_has_plan,
        'current_plan': current_plan,
        'current_plan_name': current_plan_name,
        'previous_plan_amount': previous_plan_amount
    })

from django.shortcuts import render, redirect
from .models import Plan, Payment 
from django.utils import timezone  
@custom_login_required
def payment_gateway_view(request, plan_id):
    user_id = request.session.get('user_id')
    
    try:
        plan = Plan.objects.get(plan_id=plan_id)
    except Plan.DoesNotExist:
        messages.error(request, "Plan not found.")
        return redirect('plans')

    if request.method == 'POST':
        # Process payment here
        payment = Payment(
            plan_id=plan_id,
            user_id=user_id,
            payment_date=timezone.now(),
            mode='online',
            status='success',
            active=1
        )
        payment.save()  
        messages.success(request, 'Payment Successful')
        return redirect('plans')

    # If it's a GET request, just render the payment gateway form
    return render(request, 'payment_gateway.html', {'plan': plan})

from datetime import datetime
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from .models import Payment  # Adjust according to your models

@custom_login_required
def delete_plan(request):
    if request.method == 'POST':
        # Fetch the user ID from the session
        user_id = request.session.get('user_id')
        print("User ID:", user_id)

        # Fetch the plan ID from the POST data
        plan_id = request.POST.get('plan_id')
        print("Plan ID:", plan_id)

        # Fetch the payment records associated with the user
        payment_records = Payment.objects.filter(user_id=user_id, active=1)

        # Check if there are any active payment records
        if payment_records.exists():
            for payment_record in payment_records:
                plan = Plan.objects.filter(plan_id=payment_record.plan_id).first()
                if plan:
                    # Store the plan amount in the session
                    request.session['previous_plan_amount'] = plan.amount

                # Update the active field to 0
                payment_record.active = 0
                payment_record.save()
            messages.success(request, "Your plan has been successfully deactivated.")
        else:
            messages.warning(request, "No active plan found for deactivation.")

        # Redirect to the plans page
        return redirect('plans')  # Adjust the redirect as needed

    # If not a POST request, redirect to plans
    return redirect('plans')


from django.shortcuts import redirect
@custom_login_required
def select_plan_view(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        user_id=request.session.get('user_id')
        # You can add any additional logic here if needed
        return redirect('payment_gateway', plan_id=plan_id)
    return redirect('plans')

def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username == 'admin001' and password == 'admin001':
            request.session['admin_username'] =username
            request.session['admin_password'] =password  
            return redirect('admin_home')
    return render(request, 'admin_login.html')

@admin_custom_login_required
def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')


@admin_custom_login_required
def admin_home_view(request):
    # Get statistics for the dashboard
    total_users = Client.objects.filter(status=1).count()
    total_orders = Order.objects.count()
    total_trainers = FitnessManager.objects.filter(status=1).count()

    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_trainers': total_trainers,
    }
    return render(request, 'admin_home.html', context)
@admin_custom_login_required
def admin_users_view(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT user_id, name, email, phone, username, date_joined
            FROM client where status=1 """)
        clients = cursor.fetchall()
        clients = [
            {
                'user_id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3],
                'username': row[4],
                'date_joined': row[5],
            } 
            for row in clients
        ]

        cursor.execute("""
            SELECT user_id, name, email, phone, username, date_joined
            FROM client where status=0 """)
        rm_clients = cursor.fetchall()
        rm_clients = [
            {
                'user_id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3],
                'username': row[4],
                'date_joined': row[5],
            } 
            for row in rm_clients
        ]
        context = {
        'clients': clients,
        'rm_clients': rm_clients,
    }
    return render(request, 'admin_users.html',context)
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

from django.conf import settings
from django.shortcuts import render
from django.db import connection

@admin_custom_login_required
def admin_fm_view(request):
    with connection.cursor() as cursor:
        # Fetch fitness managers without a username and password
        cursor.execute("""
            SELECT fm.user_id, fm.name, fm.email, fm.phone, q.qualification, d.designation, fm.certificate_proof 
    FROM tbl_fitness_manager fm
    JOIN tbl_qualifications q ON fm.qualification_id = q.qualification_id
    JOIN tbl_designations d ON fm.designation_id = d.designation_id
    WHERE fm.username = '' AND fm.password = ''
        """)
        applicants = cursor.fetchall()
        applicants = [
            {
                'user_id': row[0],
        'name': row[1],
        'email': row[2],
        'phone': row[3],
        'qualification': row[4],
        'designation': row[5],
        'certificate_proof': row[6],
            } 
            for row in applicants
        ]
        
        # Fetch fitness managers with a username and password
        cursor.execute("""
            SELECT fm.user_id, fm.name, fm.email, fm.phone, q.qualification, d.designation, 
           fm.certificate_proof, fm.username, fm.password
    FROM tbl_fitness_manager fm
    JOIN tbl_qualifications q ON fm.qualification_id = q.qualification_id
    JOIN tbl_designations d ON fm.designation_id = d.designation_id
    WHERE fm.username != '' AND fm.password != '' AND fm.status = 1
        """)
        complete_fms = cursor.fetchall()
        complete_fms = [
            {
                'user_id': row[0],
        'name': row[1],
        'email': row[2],
        'phone': row[3],
        'qualification': row[4],  # Updated to qualification_name
        'designation': row[5],    # Updated to designation_name
        'certificate_proof': row[6],
        'username': row[7],
        'password': row[8],
            }
            for row in complete_fms
        ]
        
        cursor.execute("""
            SELECT fm.user_id, fm.name, fm.email, fm.phone, q.qualification, d.designation, 
           fm.certificate_proof, fm.username, fm.password
    FROM tbl_fitness_manager fm
    JOIN tbl_qualifications q ON fm.qualification_id = q.qualification_id
    JOIN tbl_designations d ON fm.designation_id = d.designation_id
    WHERE fm.status = 0
        """)
        removed_fms = cursor.fetchall()
        removed_fms = [
            {
                'user_id': row[0],
        'name': row[1],
        'email': row[2],
        'phone': row[3],
        'qualification': row[4],  # Updated to qualification_name
        'designation': row[5],    # Updated to designation_name
        'certificate_proof': row[6],
        'username': row[7],
        'password': row[8],
            }
            for row in removed_fms
        ]

    context = {
        'applicants': applicants,
        'complete_fms': complete_fms,
        'removed_fms' : removed_fms,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'admin_fm.html', context)

def delete_fm(request, user_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE tbl_fitness_manager SET status=0 WHERE user_id = %s", [user_id])
    messages.success(request, "Deleted...!")
    return redirect('admin_fm' )
def delete_client(request, user_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE client SET status=0 WHERE user_id = %s", [user_id])
    return redirect('admin_users')

def accept_fm_view(request, user_id):
    with connection.cursor() as cursor:
        username = get_random_string(8)
        password = get_random_string(12) 
        
        cursor.execute("SELECT email FROM tbl_fitness_manager WHERE user_id = %s", [user_id])
        email = cursor.fetchone()[0]

        cursor.execute("""
            UPDATE tbl_fitness_manager
            SET username = %s, password = %s
            WHERE user_id = %s
        """, [username, password, user_id])

        send_mail(
            'Congratulations... You are Seleceted as Fitness Manager In FITSCULPT'
            'Your Fitness Manager Account Credentials',
            f'Your account has been approved.\nUsername: {username}\nPassword: {password}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    messages.success(request, "The credentials has been sent.")

    return redirect('admin_fm')  

from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect, render
from django.db import connection
from django.contrib import messages
from datetime import datetime, timedelta

def interview_fm_view(request, user_id):
    if request.method == 'POST':
        action = request.POST.get('action')  # Get the action (accept or reject)
        meet_link = request.POST.get('meet_link')
        interview_time=request.POST.get('interview_time')  # Get the Google Meet link if provided

        with connection.cursor() as cursor:
            # Fetch the email, date_joined, and interview_status from the database
            cursor.execute("SELECT email, date_joined, interview_status FROM tbl_fitness_manager WHERE user_id = %s", [user_id])
            result = cursor.fetchone()
            print(result)
            if result:
                email, date_joined, interview_status = result

                if interview_status == 'scheduled':
                    messages.info(request, "Interview already scheduled.")
                    return redirect('admin_fm')

                if interview_status == 'rejected':
                    messages.info(request, "Registration already rejected.")
                    return redirect('admin_fm')

                if action == 'accept':
                    if not meet_link:
                        messages.error(request, "Please provide a Google Meet link.")
                        return redirect('interview_fm', user_id=user_id)
                if action == 'accept':
                    if not interview_time:
                        messages.error(request, "Please provide Interview Date & Time.")
                        return redirect('interview_fm', user_id=user_id)

                    # Calculate the interview date (two days after date_joined at 10:00 AM)
                    interview_date = datetime.strptime(interview_time, '%Y-%m-%dT%H:%M')


                    # Format the interview date as a readable string
                    interview_datetime_str = interview_date.strftime('%Y-%m-%d %H:%M:%S')
                    print(interview_datetime_str)

                    # Send acceptance email with the Google Meet link and interview date
                    send_mail(
                        subject='Your Interview has been scheduled From FITSCULPT',
                        message=f'Greeting from FITSCULPT .Dear candidate, your interview has been scheduled for {interview_datetime_str}. Please join the meeting using the following link: {meet_link}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )

                    # Update the interview status to 'scheduled'
                    cursor.execute("UPDATE tbl_fitness_manager SET interview_status = 'scheduled', interview_time=%s  WHERE user_id = %s", [interview_datetime_str,user_id])

                    messages.success(request, "Interview scheduled and email sent.")
                elif action == 'reject':
                    # Send rejection email
                    send_mail(
                        subject='Registration Rejected',
                        message='Dear candidate, your registration has been rejected.Thank You . From FITSCULPT',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )

                    # Update the interview status to 'rejected'
                    cursor.execute("UPDATE tbl_fitness_manager SET status = 0 WHERE user_id = %s", [user_id])

                    messages.success(request, "Registration rejected and email sent.")
            else:
                messages.error(request, "Mail id not found")

        return redirect('admin_fm')  # Redirect to the appropriate page after processing
    else:
        return redirect('admin_fm')  # Handle non-POST requests appropriately




 
 
@admin_custom_login_required
def view_certificate(request, user_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT certificate_proof FROM tbl_fitness_manager WHERE user_id = %s", [user_id])
        certificate_proof = cursor.fetchone()[0]
    
    certificate_url = settings.MEDIA_URL + certificate_proof
    print(certificate_url)
    file_extension = os.path.splitext(certificate_proof)[1]
    
    return render(request, 'media.html', {'certificate_url': certificate_url})
@custom_login_required
def view_workout_img(request, workout_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT workout_image, reference_video,workout_name FROM tbl_workouts WHERE workout_id = %s", [workout_id])

        result = cursor.fetchone()

        if result:
            workout_image, reference_video,workout_name = result
        else:
            workout_image, reference_video,workout_name = None, None, None

    context = {
    'workout_image': workout_image,
    'reference_video': reference_video,
    'workout_name':workout_name,
}

    workout_url = settings.MEDIA_URL + workout_image
    print(workout_url)
    
    return render(request, 'workout_media.html', {'workout_url': workout_url, 'reference_video': reference_video,'workout_name':workout_name})

from django.shortcuts import render, redirect
from .models import Workout
from django.core.files.storage import FileSystemStorage
@fm_custom_login_required
def fm_workouts_view(request):
    return render(request, 'fm_workouts.html')
@fm_custom_login_required
def see_all_workouts(request):
    workouts = Workout.objects.all()
    return render(request, 'fm_workouts.html', {'workouts': workouts})


from django.shortcuts import render, redirect
from .models import Workout, Plan, Service
from django.core.files.storage import FileSystemStorage

@fm_custom_login_required
def add_workout(request):
    if request.method == 'POST':
        # Get form data
        workout_name = request.POST['workout_name']
        description = request.POST['description']
        body_part = request.POST['body_part']
        duration = request.POST['duration']
        workout_image = request.FILES['workout_image']
        reference_video=request.POST['reference_video']

        if Workout.objects.filter(workout_name=workout_name).exists():
            # Workout already exists, add an error message
            error_message = f"The workout '{workout_name}' already exists."
            plans = Plan.objects.all()  # Fetch available plans again
            return render(request, 'add_workout.html', {'plans': plans, 'error_message': error_message})
        
        # Save the workout details and get the workout_id
        workout = Workout(
            workout_name=workout_name,
            description=description,
            body_part=body_part,
            duration=duration,
            workout_image=workout_image,
            reference_video=reference_video
        )
        workout.save()  # This saves the workout and assigns the workout_id
        workout_id = workout.workout_id  # Get the auto-incremented workout_id
        messages.success(request, "Workout Added")


        # Get the selected plans from the form
        selected_plans = request.POST.getlist('plans')
        
        for plan_id in selected_plans:
            plan = Plan.objects.get(plan_id=plan_id)
            
            # Create Service for each selected plan
            if plan.plan_name == 'Basic Plan':
                service_no = 1
                service_type = 'Basic'
                service_description = 'Basic plan including 5 workouts for each body part'
                category = 'plan 1'
            elif plan.plan_name == 'Standard Plan':
                service_no = 2
                service_type = 'Standard'
                service_description = 'Standard plan including 7 workouts for each body part'
                category = 'plan 2'
            elif plan.plan_name == 'Premium Plan':
                service_no = 3
                service_type = 'Premium'
                service_description = 'Premium plan including 9 workouts for each body part'
                category = 'plan 3'
            elif plan.plan_name == 'Child Plan':
                service_no = 4
                service_type = 'Child'
                service_description = 'Child plan including 4 workouts for each body part'
                category = 'plan 4'
            
            service = Service(
                service_no=service_no,
                service_type=service_type,
                workout_id=workout_id,  # Use workout_id here
                nutrition_no=5,  # Example value, you can modify this
                description=service_description,
                category=category,
                day=1 if body_part.strip().lower() == 'chest' else   # Day 1 for chest
        2 if body_part.strip().lower() == 'back' else    # Day 2 for back
        3 if body_part.strip().lower() == 'biceps' else  # Day 3 for biceps
        4 if body_part.strip().lower() == 'triceps' else # Day 4 for triceps
        5 if body_part.strip().lower() == 'shoulder' else# Day 5 for shoulder
        6 if body_part.strip().lower() == 'leg' else 0     # Day 6 for leg
            )
            service.save()
        
        # Redirect to workout list page after submission
        return redirect('see_all_workouts')
    
    # Fetch available plans from the database
    plans = Plan.objects.all()
    return render(request, 'add_workout.html', {'plans': plans})

from django.shortcuts import render, redirect
from .models import Workout, Plan, Service

@fm_custom_login_required
def update_workout(request, workout_id):
    workout = Workout.objects.get(workout_id=workout_id)

    associated_services = Service.objects.filter(workout_id=workout_id)
    associated_service_nos = [service.service_no for service in associated_services]
    all_plans = Plan.objects.all()
    associated_plans = Plan.objects.filter(service_no__in=associated_service_nos)

    if request.method == 'POST':
        selected_plan_ids = request.POST.getlist('plans')  # Get selected plan IDs from the form
        
        # Update the workout details
        workout.workout_name = request.POST.get('workout_name', workout.workout_name)
        workout.description = request.POST.get('description', workout.description)
        workout.body_part = request.POST.get('body_part', workout.body_part)
        workout.duration = request.POST.get('duration', workout.duration)
        workout.reference_video=request.POST.get('reference_video',workout.reference_video)

        # Handle the workout image if provided
        if 'workout_image' in request.FILES:
            workout.workout_image = request.FILES['workout_image']

        workout.save()  # Save updated workout details
        messages.success(request, "Workout Updated")


        # Delete existing services for this workout
        Service.objects.filter(workout_id=workout_id).delete()

        # Create new services based on selected plans
        for plan_id in selected_plan_ids:
            plan = Plan.objects.get(plan_id=plan_id)

            service_no = 0
            service_type = ''
            service_description = ''
            category = ''

            if plan.plan_name == 'Basic Plan':
                service_no = 1
                service_type = 'Basic'
                service_description = 'Basic plan including 5 workouts for each body part'
                category = 'plan 1'
            elif plan.plan_name == 'Standard Plan':
                service_no = 2
                service_type = 'Standard'
                service_description = 'Standard plan including 7 workouts for each body part'
                category = 'plan 2'
            elif plan.plan_name == 'Premium Plan':
                service_no = 3
                service_type = 'Premium'
                service_description = 'Premium plan including 9 workouts for each body part'
                category = 'plan 3'
            elif plan.plan_name == 'Child Plan':
                service_no = 4
                service_type = 'Child'
                service_description = 'Child plan including 4 workouts for each body part'
                category = 'plan 4'

            day = {
                'chest': 1,
                'back': 2,
                'biceps': 3,
                'triceps': 4,
                'shoulder': 5,
                'leg': 6
            }.get(workout.body_part.strip().lower(), 0)  

            service = Service(
                service_no=service_no,
                service_type=service_type,
                workout_id=workout_id,
                nutrition_no=5,  # You can set this dynamically if needed
                description=service_description,
                category=category,
                day=day
            )
            service.save()

        return redirect('see_all_workouts')  # Redirect to workout list after update

    context = {
        'workout': workout,
        'all_plans': all_plans,  # All available plans
        'associated_plans': associated_plans,  # Plans already linked to the workout
    }

    return render(request, 'update_workout.html', context)




@fm_custom_login_required
def delete_workout(request, workout_id):
    workout = Workout.objects.get(workout_id=workout_id)
    if request.method == 'POST':
        workout.delete()
        messages.success(request, "Workout Deleted...!")

        return redirect('see_all_workouts')

    return redirect(request, 'delete_workout', {'workout': workout})  # Confirm delete



from django.shortcuts import render, redirect
from .models import Workout
from django.core.files.storage import FileSystemStorage
@fm_custom_login_required
def fm_nutritions_view(request):
    return render(request, 'fm_nutritions.html')
@fm_custom_login_required
def see_all_food(request):
    foods = FoodDatabase.objects.all()
    return render(request, 'fm_nutritions.html', {'foods': foods})

@fm_custom_login_required
def search_food(request):
    query = request.GET.get('q')  # Get the search query from the form

    if query:
        # Search for the food by name
        foods = FoodDatabase.objects.filter(food_name__icontains=query)
        
        # Fetch nutritional details for each food
        food_with_nutrition = []
        for food in foods:
            # Get all related nutritional entries for the food
            nutrition_details = Nutrition.objects.filter(food_id=food.food_id)
            food_with_nutrition.append({
                'food': food,
                'nutrition': nutrition_details
            })
        
        if foods.exists():
            return render(request, 'fm_nutritions_search_results.html', {'food_with_nutrition': food_with_nutrition})
        else:
            return render(request, 'fm_nutritions_search_results.html', {'error_message': 'No food found matching your query.'})
    else:
        return redirect('see_all_food')  # Redirect if no query


@fm_custom_login_required
def search_workout(request):
    query = request.GET.get('q')  # Get the search query from the form

    if query:
        # Search for the workouts by name
        workouts = Workout.objects.filter(workout_name__icontains=query)
        print(workouts)

        if workouts.exists():
            # Instead of looping through workouts, just use them directly
            return render(request, 'fm_workouts_search_results.html', {'workout_details': workouts})
        else:
            return render(request, 'fm_workouts_search_results.html', {'error_message': 'No workout found matching your query.'})
    else:
        return redirect('see_all_workouts')



@fm_custom_login_required
def add_food(request):
    # Fetch unique nutrition_no and their descriptions
    nutrition_options = Nutrition.objects.values('nutrition_no').annotate(
        first_description=models.F('description')
    ).distinct()

    if request.method == 'POST':
        food_name = request.POST['food_name']
        food_type = request.POST['food_type']
        calories = request.POST['calories']
        proteins = request.POST['proteins']
        carbs = request.POST['carbs']
        fats = request.POST['fats']

        if FoodDatabase.objects.filter(food_name=food_name).exists():
            error_message = "This food already exists. Please enter a different food name."
            context = {
                'nutrition_options': nutrition_options,
                'error_message': error_message,
            }
            return render(request, 'add_food.html', context)
        # Create the food entry
        food = FoodDatabase(
            food_name=food_name,
            food_type=food_type,
            calories=calories,
            proteins=proteins,
            carbs=carbs,
            fats=fats
        )
        food.save()  # Save the food entry
        messages.success(request, "Food Added")

        food_id = food.food_id  # Get the newly created food_id
        print(food_id)

        selected_nutrition_nos = request.POST.getlist('nutritional_descriptions')  # Get selected nutrition_nos

        # Insert entries for each selected nutrition_no
        for nutrition_no in selected_nutrition_nos:
            # Use filter() to get a queryset
            nutrition_entries = Nutrition.objects.filter(nutrition_no=nutrition_no)
            if nutrition_entries.exists():
                nutrition_entry = nutrition_entries.first()  # Get the first matching entry

                # Create a new Nutrition entry for each selected nutrition_no
                Nutrition.objects.create(
                    nutrition_no=nutrition_entry.nutrition_no,  # Store the nutrition_no
                    food_id=food_id,                             # Associate with the new food_id
                    description=nutrition_entry.description      # Fetch the description
                )

        return redirect('see_all_food')  # Redirect to see all food after adding

    context = {
        'nutrition_options': nutrition_options,
    }

    return render(request, 'add_food.html', context)





@fm_custom_login_required
def update_food(request, food_id):
    food = FoodDatabase.objects.get(food_id=food_id)
    if request.method == 'POST':
        food.food_name = request.POST['food_name']
        food.food_type = request.POST['food_type']
        food.calories = request.POST['calories']
        food.proteins = request.POST['proteins']
        food.carbs = request.POST['carbs']
        food.fats = request.POST['fats']
        food.save()
        messages.success(request, "Food Updated")

        return redirect('see_all_food')

    return render(request, 'update_food.html', {'food': food})  # Render form with workout details
@fm_custom_login_required
def delete_food(request, food_id):
    food = FoodDatabase.objects.get(food_id=food_id)
    if request.method == 'POST':
        food.delete()
        messages.success(request, "Food Deleted")

        return redirect('see_all_food')

    return render(request, 'delete_food.html', {'food': food})  # Confirm delete


from django.shortcuts import render
from .models import Plan, Service, Workout
from django.db import connection

@custom_login_required
def workouts_view(request, day=None):
    user_id = request.session.get('user_id')

    # Fetch plan_id from tbl_payment
    with connection.cursor() as cursor:
        cursor.execute("SELECT plan_id FROM tbl_payment WHERE user_id = %s AND active=1 ", [user_id])
        result = cursor.fetchone()
        plan_id = result[0] if result else None

    plan = None
    workouts = []

    if plan_id:
        plan = Plan.objects.get(plan_id=plan_id)

        if day:
            services = Service.objects.filter(service_no=plan.service_no, day=day)

            for service in services:
                workout = Workout.objects.get(workout_id=service.workout_id)
                workouts.append(workout)

    # Get current date and calculate week start date
    current_date = datetime.now().date()
    week_start_date = current_date - timedelta(days=current_date.weekday())
    
    context = {
        'workouts': workouts,
        'plan': plan,
        'week_start_date': week_start_date,
        'now': current_date,
    }
    return render(request, 'workouts.html', context)



from django.shortcuts import render, get_object_or_404
from .models import Plan, Service, Workout
from django.db import connection

@custom_login_required
def workouts_by_day_view(request, day):
    user_id = request.session.get('user_id')
    current_date = datetime.now().date()
    current_datetime = datetime.now()
    week_start_date = current_date - timedelta(days=current_date.weekday())

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT plan_id 
            FROM tbl_payment 
            WHERE user_id = %s AND active = 1
        """, [user_id])
        result = cursor.fetchone()
        plan_id = result[0] if result else None

        if not plan_id:
            return render(request, 'workouts.html', {
                'error': 'No active plan found. Please Select a valid Plan'
            })

        plan = Plan.objects.get(plan_id=plan_id)

        if day > 1:
            # Check if ALL workouts from previous day are completed
            cursor.execute("""
                WITH PreviousDayWorkouts AS (
                    SELECT w.workout_id
                    FROM tbl_services s
                    JOIN tbl_workouts w ON s.workout_id = w.workout_id
                    WHERE s.service_no = %s AND s.day = %s
                ),
                CompletedWorkouts AS (
                    SELECT DISTINCT wc.workout_id
                    FROM WeeklyWorkoutCompletion wc
                    WHERE wc.client_id = %s 
                    AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
                )
                SELECT 
                    COUNT(DISTINCT pdw.workout_id) as total_workouts,
                    COUNT(DISTINCT cw.workout_id) as completed_workouts
                FROM PreviousDayWorkouts pdw
                LEFT JOIN CompletedWorkouts cw ON pdw.workout_id = cw.workout_id
            """, [plan.service_no, day-1, user_id])
            
            total_workouts, completed_workouts = cursor.fetchone()

            if completed_workouts < total_workouts:
                messages.error(request, f"Please complete all Day {day-1} workouts first")
                return redirect('workouts_by_day', day=day-1)

            # If all workouts completed, check the 24-hour gap
            if completed_workouts == total_workouts:
                cursor.execute("""
                    SELECT MAX(wc.completion_date)
                    FROM WeeklyWorkoutCompletion wc
                    JOIN tbl_services s ON wc.workout_id = s.workout_id
                    WHERE wc.client_id = %s 
                    AND s.day = %s 
                    AND s.service_no = %s
                    AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
                """, [user_id, day-1, plan.service_no])
                
                last_completion = cursor.fetchone()[0]
                if last_completion:
                    hours_passed = (current_datetime - last_completion).total_seconds() / 3600
                    if hours_passed < 24:
                        wait_hours = 24 - hours_passed
                        messages.info(request, f"Please wait {int(wait_hours)} more hours before starting next day's workout")
                        return redirect('workouts_by_day', day=day-1)

        # Check if ALL workouts for current day were completed in last 7 days
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM tbl_services WHERE service_no = %s AND day = %s) as total_workouts,
                COUNT(DISTINCT wc.workout_id) as completed_workouts,
                MAX(wc.completion_date) as last_completion_date
            FROM tbl_services s
            LEFT JOIN WeeklyWorkoutCompletion wc ON s.workout_id = wc.workout_id 
                AND wc.client_id = %s 
                AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
            WHERE s.service_no = %s AND s.day = %s
        """, [plan.service_no, day, user_id, plan.service_no, day])
        
        total_workouts, completed_workouts, last_completion = cursor.fetchone()
        
        # Only show the 7-day message if ALL workouts were completed
        if completed_workouts == total_workouts and last_completion:
            next_available = datetime.strptime(str(last_completion), '%Y-%m-%d %H:%M:%S') + timedelta(days=7)
            if current_datetime < next_available:
                messages.info(request, f"This day's workout will be available on {next_available.strftime('%A, %B %d')}")
                return redirect('workouts')

        # Get workouts with their completion status
        cursor.execute("""
            SELECT 
                w.*, 
                DATE_FORMAT(wc.completion_date, '%%Y-%%m-%%d %%H:%%i:%%s') as completion_date
            FROM tbl_services s
            JOIN tbl_workouts w ON s.workout_id = w.workout_id
            LEFT JOIN WeeklyWorkoutCompletion wc ON w.workout_id = wc.workout_id 
                AND wc.client_id = %s 
                AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
            WHERE s.service_no = %s AND s.day = %s
        """, [user_id, plan.service_no, day])

        workouts = []
        for row in cursor.fetchall():
            workout = {
                'workout_id': row[0],
                'workout_name': row[1],
                'description': row[2],
                'body_part': row[3],
                'duration': row[4],
                'workout_image': row[5],
                'reference_video': row[6],
                'completion_date': datetime.strptime(row[7], '%Y-%m-%d %H:%M:%S') if row[7] else None
            }
            workouts.append(workout)

        context = {
            'plan': plan,
            'workouts': workouts,
            'week_start_date': week_start_date,
            'now': current_datetime,
            'current_day': day
        }
        return render(request, 'workouts.html', context)

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import FitnessManager, ClientFM
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from .models import ClientFM

from django.contrib import messages

@custom_login_required
def personal_workout_view(request):
    user_id = request.session.get('user_id')
    client_id = user_id  
    
    selected_trainer = ClientFM.objects.filter(client_id=client_id).first()

    if not selected_trainer:
        messages.error(request, "You have not selected a trainer yet. Please select a trainer to continue.")
        return redirect('select_trainer')
    fm_skills = FMSkills.objects.filter(fm_id=selected_trainer.fm_id).first()

    context = {
        'trainer_selected': selected_trainer,
        'fm_skills': fm_skills
    }
    return render(request, 'personal_workout.html', context)
from django.db.models import F
from django.shortcuts import redirect
from django.contrib import messages

@custom_login_required
def rate_trainer_view(request):
    if request.method == 'POST':
        fm_id = request.POST.get('fm_id')
        new_rating = int(request.POST.get('rating'))

        # Fetch the FMSkills for the selected trainer
        fm_skills = FMSkills.objects.filter(fm_id=fm_id).first()

        if fm_skills:
            # Update the rating by calculating the new average
            existing_rating = fm_skills.rating
            rating_count = fm_skills.rating_count if fm_skills.rating_count else 1  # Assuming `rating_count` field exists to track number of ratings

            # Calculate the new average rating
            updated_rating = (existing_rating * rating_count + new_rating) / (rating_count + 1)

            # Update the FMSkills record with new rating and increment rating_count
            fm_skills.rating = round(updated_rating, 1)  # Rounding to 1 decimal place
            fm_skills.rating_count = F('rating_count') + 1
            fm_skills.save()

            messages.success(request, f'Thank you! You rated this trainer {new_rating}/5. The average rating is now {fm_skills.rating}/5.')
        else:
            messages.error(request, "Trainer not found or invalid ID.")

    return redirect('personal_workout')


from django.shortcuts import render
from .models import FitnessManager, ClientFM, Designations
from django.db.models import Q

@custom_login_required
def select_trainer_view(request):
    user_id = request.session.get('user_id')
    if user_id is None:
        messages.error(request, "User not logged in.")
        return redirect('login')  # Redirect to your login page

    client_id = user_id  

    try:
        client = Client.objects.get(user_id=client_id)
    except Client.DoesNotExist:
        messages.error(request, "Client not found.")
        return redirect('login')  # Redirect to an appropriate error page
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT plan_id FROM tbl_payment WHERE user_id = %s AND active=1", [user_id])
        result = cursor.fetchone()
        plan_id = result[0] if result else None

    has_active_plan = plan_id is not None

    if request.method == 'POST' and has_active_plan:
        trainer_id = request.POST.get('trainer_id')
        selected_time = request.POST.get('timing')

        if not selected_time:
            messages.error(request, "Timing cannot be empty.")
            return redirect('select_trainer')

        # Update or create a new ClientFM record
        selected_trainer = ClientFM.objects.filter(client_id=client_id).first()

        try:
            fitness_manager = FitnessManager.objects.get(user_id=trainer_id)
        except FitnessManager.DoesNotExist:
            messages.error(request, "Selected trainer does not exist.")
            return redirect('select_trainer')

        if selected_trainer:
            selected_trainer.fm_id = trainer_id
            selected_trainer.timing = selected_time
            selected_trainer.client_name = client.name  # Ensure this field is updated
            selected_trainer.fm_name = fitness_manager.name
            selected_trainer.status=0
              # Ensure this field is updated
            selected_trainer.save()
        else:
            ClientFM.objects.create(
                client_id=client_id,
                fm_id=trainer_id,
                timing=selected_time,
                client_name=client.name, 
                fm_name=fitness_manager.name,    
                status=0,
                class_time=datetime.now()
            )
        messages.success(request, 'Selected Trainer successfully')

        return redirect('personal_workout')

    # Get fitness managers with designation_id = 2 or 5 and status = 1
    fitness_managers = FitnessManager.objects.filter(
        Q(designation_id=5) | 
        Q(designation_id=2),
        status=1
    )

    # Fetch the designations with id 2 and 5
    designations = Designations.objects.filter(designation_id__in=[2, 5])
    designation_map = {designation.designation_id: designation.designation for designation in designations}

    qualifications = Qualifications.objects.filter(qualification_id__in=[2, 5])
    qualification_map = {qualification.qualification_id: qualification.qualification for qualification in qualifications}

    # Predefined time slots in the format '6 AM', '7 AM', etc.
    predefined_times = ['6 AM', '7 AM', '8 AM', '5 PM', '6 PM', '7 PM'] 
    
    # Determine assigned times for trainers
    trainers_with_details = []
    for trainer in fitness_managers:
        assigned_sessions = ClientFM.objects.filter(fm_id=trainer.user_id).values_list('timing', flat=True)
        assigned_times = set(assigned_sessions)  # Convert to set for efficient lookup

        # Filter available times
        available_times = [time for time in predefined_times if time not in assigned_times]
        fm_skills = FMSkills.objects.filter(fm_id=trainer.user_id).first()
        print(fm_skills)

        trainers_with_details.append({
            'trainer': trainer,
            'available_times': available_times,  # Pass available times to the template
            'designation': designation_map.get(trainer.designation_id, 'Unknown') ,
             'qualification': qualification_map.get(trainer.qualification_id, 'Unknown'),
             'fm_skills': fm_skills 
              # Fetch corresponding designation name
        })

    context = {
        'trainers_with_details': trainers_with_details,
        'has_active_plan': has_active_plan,
    }
    return render(request, 'select_trainer.html', context)

from django.shortcuts import render, get_object_or_404
from .models import FMSkills
from django.http import Http404

@custom_login_required
def fm_skills_view2(request, fm_id):
    try:
        # Fetch the FMSkills for the selected fitness manager
        fm_skills = FMSkills.objects.get(fm_id=fm_id)
    except FMSkills.DoesNotExist:
        # Handle the case where no FMSkills exists for the given fm_id
        return render(request, 'fm_skills_detail.html', {
            'error_message': f"No Additional details found for the fitness manager."
        })

    context = {
        'fm_skills': fm_skills
    }
    return render(request, 'fm_skills_detail.html', context)




@admin_custom_login_required
def view_sessions_view(request):
    sessions = ClientFM.objects.filter(status=1)
    mental_fitness_sessions = MentalFitness.objects.filter(status=1) 
    return render(request, 'view_sessions.html', {
        'sessions': sessions,
        'mental_fitness_sessions': mental_fitness_sessions
    })



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ClientFM, FitnessManager, Client

@fm_custom_login_required
def set_live_session_view(request):
    user_id = request.session.get('fm_user_id')
    clients = Client.objects.all()

    if not user_id:
        messages.error(request, "User not authenticated.")
        return redirect('fm_login')

    try:
        fitness_manager = FitnessManager.objects.get(user_id=user_id)
    except FitnessManager.DoesNotExist:
        messages.error(request, "Fitness Manager does not exist. Please contact support.")
        return redirect('set_live_session')

    if request.method == 'POST':
        class_link = request.POST.get('class_link')
        selected_client_id = request.POST.get('client_id')
        class_time_str = request.POST.get('class_time')
        if class_time_str:
            try:
                class_time_naive = datetime.strptime(class_time_str, '%Y-%m-%dT%H:%M')

                class_time = timezone.make_aware(class_time_naive, timezone.get_current_timezone())

                if class_time < timezone.now():
                    messages.error(request, "Class time cannot be set in the past. Please select a future date and time.")
                    return redirect('set_live_session')
            except ValueError:
                messages.error(request, "Invalid date and time format. Please select a valid date and time.")
                return redirect('set_live_session')
        else:
            messages.error(request, "Class time is required.")
            return redirect('set_live_session')
        try:
            client_fm = ClientFM.objects.get(client_id=selected_client_id, fm_id=fitness_manager.user_id)
            client_fm.class_link = class_link
            client_fm.class_time = class_time
            client_fm.status=1
            client_fm.save()
            messages.success(request, "Class link updated successfully.")
        except ClientFM.DoesNotExist:
            messages.error(request, "Client not found or not assigned to you.")
        except ValueError:
            messages.error(request, "Invalid class time format.")
        
        return redirect('set_live_session')

    # Get ClientFM entries for this fitness manager
    clients = ClientFM.objects.filter(fm_id=fitness_manager.user_id)

    if not clients.exists():
        messages.info(request, "No clients have selected you as their fitness manager.")

    context = {
        'fitness_manager': fitness_manager,
        'clients': clients,
    }
    return render(request, 'set_live_session.html', context)

@fm_custom_login_required
def join_session(request):
    fm_id = request.session.get('fm_user_id')

    if not fm_id:
        messages.error(request, "User not authenticated.")
        return redirect('fm_login')

    active_sessions = ClientFM.objects.filter(fm_id=fm_id, status=1)

    context = {
        'active_sessions': active_sessions,
    }

    return render(request, 'join_session.html', context)


from django.shortcuts import render, get_object_or_404


@fm_custom_login_required
def view_client_details(request, client_id):
    user_id = request.session.get('fm_user_id')
    
    if not user_id:
        messages.error(request, "User not authenticated.")
        return redirect('fm_login')
    
    # Retrieve the client based on the provided client_id
    client = get_object_or_404(Client, user_id=client_id)
    goals = Goal.objects.filter(user_id=client_id)
    progress=Progress.objects.filter(user_id=client_id)

    context = {
        'client': client,
        'goals': goals,
        'progress':progress
    }
    return render(request, 'view_client_details.html', context)



from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

@custom_login_required 
def view_scheduled_class(request):
    user_id = request.session.get('user_id')

    client_schedule = ClientFM.objects.filter(client_id=user_id,status=1).first()

    if client_schedule:
        context = {
            'client_schedule': client_schedule,
        }
        return render(request, 'view_scheduled_class.html', context)
    else:
        return render(request, 'view_scheduled_class.html', {'client_schedule': None})



@custom_login_required
def personal_nutrition_view(request):
    user_id = request.session.get('user_id')
    client_id = user_id  
    print(client_id)
    selected_dietitian = ClientFM2.objects.filter(client_id=client_id).first()
    if not selected_dietitian:
        messages.error(request, "You have not selected a dietitian yet. Please select a dietitian to continue.")
        return redirect('select_dietitian')

    context = {
        'dietitian_selected': selected_dietitian
    }
    return render(request, 'personal_nutrition.html', context)


from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Client
from .models import FitnessManager, ClientFM2  # Import your models
from .models import FitnessManager, Qualifications, Designations, ClientFM2

from django.shortcuts import render, redirect
from .models import FitnessManager, ClientFM2, Client, Designations, Qualifications

@custom_login_required
def select_dietitian_view(request):
    user_id = request.session.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("SELECT plan_id FROM tbl_payment WHERE user_id = %s AND active=1", [user_id])
        result = cursor.fetchone()
        plan_id = result[0] if result else None

    # If there's no active plan, set a flag to prevent selection
    plan = None
    workouts = []
    if plan_id:
        plan = Plan.objects.get(plan_id=plan_id)

    # Fetch the client's name based on the logged-in user's ID
    try:
        client = Client.objects.get(user_id=user_id)
        client_name = client.name  # Assuming 'fname' is the field for the client's name
    except Client.DoesNotExist:
        client_name = None

    # Fetch fitness managers with specified qualifications and status
    fitness_managers = FitnessManager.objects.filter(qualification_id=3, designation_id=3, status=1)

    # Create a list to hold the fitness manager details with designation and qualification
    fm_details = []
    for fm in fitness_managers:
        designation = Designations.objects.get(designation_id=fm.designation_id)
        qualification = Qualifications.objects.get(qualification_id=fm.qualification_id)
        client_count = ClientFM2.objects.filter(fm_id=fm.user_id).count()
        if client_count < 4:
            fm_details.append({
                'fm': fm,
                'designation': designation.designation,
                'qualification': qualification.qualification,
                'client_count': client_count,  # Add client count for display if needed
            })

    if request.method == 'POST':
        selected_fm_id = request.POST.get('fitness_manager')
        if selected_fm_id:
            selected_fm_client_count = ClientFM2.objects.filter(fm_id=selected_fm_id).count()
            if selected_fm_client_count >= 4:
                messages.error(request, 'This Dietitian has already reached the maximum number of clients.')
            # Create a new entry in ClientFM2
            else:
                ClientFM2.objects.create(
                client_id=user_id,
                fm_id=selected_fm_id,
                client_name=client_name,
                fm_name=FitnessManager.objects.get(user_id=selected_fm_id).name
            )
            messages.success(request, 'Selected the Dietitian successfully')
            return redirect('personal_nutrition')  # Redirect to a success page or wherever you want
            

    return render(request, 'select_dietitian.html', {
        'fitness_managers': fm_details,  # Pass the detailed fitness manager list
        'client_name': client_name,
         'has_plan': plan_id is not None,
    })



from django.shortcuts import render, redirect
from .models import Client, Nutrition, FoodDatabase
from django.db.models import Q

@custom_login_required
def nutrition_view(request):
    user_id = request.session.get('user_id')
    current_datetime = datetime.now()
    
    # Get the current day from request, defaulting to 1
    try:
        current_day = int(request.GET.get('day', 1))
        current_day = max(1, min(current_day, 7))  # Ensure day is between 1 and 7
    except (ValueError, TypeError):
        current_day = 1

    with connection.cursor() as cursor:
        # Get user's plan and nutrition details
        cursor.execute("""
            SELECT p.plan_id, p.plan_name, p.service_no 
            FROM tbl_payment t
            JOIN tbl_plans p ON t.plan_id = p.plan_id
            WHERE t.user_id = %s AND t.active = 1
        """, [user_id])
        plan_result = cursor.fetchone()
        
        if not plan_result:
            return render(request, 'nutritions.html', {'error': 'No active plan found'})
            
        plan_id, plan_name, service_no = plan_result

        # Get client's BMI category
        cursor.execute("""
            SELECT height, weight, food_type 
            FROM client 
            WHERE user_id = %s
        """, [user_id])
        height, weight, food_type = cursor.fetchone()
        
        height_in_meters = height / 100 if height else None
        bmi = weight / (height_in_meters ** 2) if weight and height else None

        if bmi:
            if bmi < 18.5:
                nutrition_category = 'Underweight'
            elif 18.5 <= bmi < 24.9:
                nutrition_category = 'Normal'
            elif 25 <= bmi < 29.9:
                nutrition_category = 'Overweight'
            else:
                nutrition_category = 'Obesity'
        else:
            return render(request, 'nutritions.html', {'error': 'Please update your profile to get nutrition suggestions.'})

        # Check Day 1 completion and time passed - Modified query
        cursor.execute("""
            SELECT MAX(wnc.completion_date) as completion_date
            FROM WeeklyNutritionCompletion wnc
            JOIN tbl_nutritions n ON wnc.nutrition_id = n.nutrition_id
            WHERE wnc.client_id = %s 
            AND n.nutrition_no = 1
            AND wnc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, [user_id])
        
        day1_result = cursor.fetchone()
        
        # Initialize variables
        is_day_1_completed = False
        can_start_day_2 = False
        hours_passed = 0

        if day1_result and day1_result[0]:  # Check if we got a valid completion date
            is_day_1_completed = True
            completion_time = day1_result[0]
            hours_passed = (current_datetime - completion_time).total_seconds() / 3600
            can_start_day_2 = hours_passed >= 24
            print(f"Debug - Hours passed: {hours_passed}, Can start day 2: {can_start_day_2}")  # Debug print

        # Get completion status for all days
        cursor.execute("""
            SELECT DISTINCT n.nutrition_no
            FROM WeeklyNutritionCompletion wnc
            JOIN tbl_nutritions n ON wnc.nutrition_id = n.nutrition_id
            WHERE wnc.client_id = %s
            AND wnc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, [user_id])
        completed_days = {row[0] for row in cursor.fetchall()}
        print(f"Debug - Completed days: {completed_days}")  # Debug print

        # Get available days with modified logic
        available_days = {1: True}  # Day 1 is always available
        
        # If Day 1 is completed and 24 hours have passed, make Day 2 available
        if is_day_1_completed and can_start_day_2:
            available_days[2] = True
            print("Debug - Day 2 marked as available")  # Debug print

        # For days 3-7, check if previous day is completed
        for day in range(3, 8):
            if day - 1 in completed_days:
                # Get the completion time of the previous day
                cursor.execute("""
                    SELECT MAX(wnc.completion_date)
                    FROM WeeklyNutritionCompletion wnc
                    JOIN tbl_nutritions n ON wnc.nutrition_id = n.nutrition_id
                    WHERE wnc.client_id = %s 
                    AND n.nutrition_no = %s
                    AND wnc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
                """, [user_id, day - 1])
                prev_day_completion = cursor.fetchone()[0]
                
                if prev_day_completion:
                    hours_since_prev = (current_datetime - prev_day_completion).total_seconds() / 3600
                    if hours_since_prev >= 24:
                        available_days[day] = True

        # Get nutrition details for current day
        cursor.execute("""
            SELECT 
                n.nutrition_id,
                n.description as nutrition_description,
                f.food_name,
                f.calories,
                f.proteins,
                f.carbs,
                f.fats
            FROM tbl_nutritions n
            JOIN tbl_food_database f ON n.food_id = f.food_id
            WHERE n.nutrition_no = %s
            ORDER BY n.nutrition_id
        """, [current_day])
        
        food_details = dictfetchall(cursor)

    context = {
        'plan': {'plan_name': plan_name},
        'food_details': food_details,
        'current_day': current_day,
        'bmi': bmi,
        'nutrition_category': nutrition_category,
        'available_days': available_days,
        'completed_days': completed_days,
        'is_day_1_completed': is_day_1_completed,
        'can_start_day_2': can_start_day_2,
        'hours_passed': hours_passed
    }
    
    # Debug print final context values
    print(f"Debug - Final context: is_day_1_completed={is_day_1_completed}, can_start_day_2={can_start_day_2}, hours_passed={hours_passed}")
    
    # After successful completion, you might want to automatically show the next day
    if 'day' not in request.GET and current_day < 7:
        last_completed = max(completed_days) if completed_days else 0
        if last_completed > 0 and last_completed < 7:
            next_day = last_completed + 1
            if next_day in available_days:
                current_day = next_day

    context = {
        'plan': {'plan_name': plan_name},
        'food_details': food_details,
        'current_day': current_day,
        'bmi': bmi,
        'nutrition_category': nutrition_category,
        'available_days': available_days,
        'completed_days': completed_days,
        'is_day_1_completed': is_day_1_completed,
        'can_start_day_2': can_start_day_2,
        'hours_passed': hours_passed
    }
    
    return render(request, 'nutritions.html', context)

@custom_login_required
def mark_nutrition_completed(request, day):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        current_datetime = datetime.now()
        status = request.POST.get('status', 'completed')

        with connection.cursor() as cursor:
            # First check if ANY nutrition for this day is already completed
            cursor.execute("""
                SELECT COUNT(*) 
                FROM WeeklyNutritionCompletion wc
                JOIN tbl_nutritions n ON wc.nutrition_id = n.nutrition_id
                WHERE wc.client_id = %s 
                AND n.nutrition_no = %s
                AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
            """, [user_id, day])
            
            completion_count = cursor.fetchone()[0]
            if completion_count > 0:
                messages.error(request, f"Day {day} has already been marked as completed")
                return redirect('nutrition')

            # Get the week_start_date from Day 1's completion if it exists
            cursor.execute("""
                SELECT week_start_date
                FROM WeeklyNutritionCompletion wc
                JOIN tbl_nutritions n ON wc.nutrition_id = n.nutrition_id
                WHERE wc.client_id = %s 
                AND n.nutrition_no = 1
                AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
                LIMIT 1
            """, [user_id])
            
            week_start_result = cursor.fetchone()
            week_start_date = week_start_result[0] if week_start_result else current_datetime.date()

            # For days after day 1, check if previous day is completed
            if day > 1:
                cursor.execute("""
                    SELECT completion_date
                    FROM WeeklyNutritionCompletion wc
                    JOIN tbl_nutritions n ON wc.nutrition_id = n.nutrition_id
                    WHERE wc.client_id = %s 
                    AND n.nutrition_no = %s
                    AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
                    ORDER BY wc.completion_date DESC
                    LIMIT 1
                """, [user_id, day - 1])
                
                result = cursor.fetchone()
                if not result:
                    messages.error(request, f"Please complete Day {day-1} first")
                    return redirect('nutrition')
                
                prev_day_completion = result[0]
                hours_passed = (current_datetime - prev_day_completion).total_seconds() / 3600
                
                if hours_passed < 24:
                    messages.error(request, f"Please wait {int(24 - hours_passed)} more hours before completing Day {day}")
                    return redirect('nutrition')

            try:
                # Start a transaction
                cursor.execute("START TRANSACTION")
                
                # Get nutrition IDs for the current day
                cursor.execute("""
                    SELECT nutrition_id 
                    FROM tbl_nutritions 
                    WHERE nutrition_no = %s
                """, [day])
                
                nutrition_ids = [row[0] for row in cursor.fetchall()]
                
                # Insert completion records using the consistent week_start_date
                completion_time = current_datetime
                for nutrition_id in nutrition_ids:
                    cursor.execute("""
                        INSERT INTO WeeklyNutritionCompletion 
                        (client_id, week_start_date, nutrition_completed, nutrition_id, completion_date)
                        VALUES (%s, %s, %s, %s, %s)
                    """, [user_id, week_start_date, status == 'completed', nutrition_id, completion_time])

                # Commit the transaction
                cursor.execute("COMMIT")
                
                messages.success(request, f"Day {day}'s nutrition plan marked as {'followed' if status == 'completed' else 'not followed'}")
                return redirect('nutrition')
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('nutrition')

    return redirect('nutrition')

@fm_custom_login_required
def fm_nutritions_view(request):
    return render(request, 'fm_nutritions.html')

@fm_custom_login_required
def fm_plans(request):
    plans = Plan.objects.all()
    return render(request, 'fm_plans.html', {'plans': plans})

@fm_custom_login_required
def fm_nutritions2(request):
    nutritions = Nutrition.objects.select_related('food').all()
    return render(request, 'fm_nutritions2.html', {'nutritions': nutritions})

@admin_custom_login_required
def admin_plans(request):
    return render(request, 'admin_plans.html')

@admin_custom_login_required
def see_all_plan(request):
    plans = Plan.objects.all()
    return render(request, 'admin_plans.html', {'plans': plans})

@admin_custom_login_required
def add_plan(request):
    if request.method == 'POST':
        plan_name = request.POST['plan_name']
        amount = request.POST['amount']
        description = request.POST['description']
        service_no = request.POST['service_no']
        
        # Check if the plan name already exists
        if Plan.objects.filter(plan_name=plan_name).exists():
            error_message = f"The plan '{plan_name}' already exists."
            plans = Plan.objects.all()  # Fetch available plans again
            return render(request, 'add_plan.html', {'plans': plans, 'error_message': error_message})

        # Check if the service number already exists
        if Plan.objects.filter(service_no=service_no).exists():
            error_message = f"The service number '{service_no}' already exists."
            plans = Plan.objects.all()  # Fetch available plans again
            return render(request, 'add_plan.html', {'plans': plans, 'error_message': error_message})

        # If no duplicates are found, save the new plan
        plan = Plan(
            plan_name=plan_name,
            amount=amount,
            description=description,
            service_no=service_no
        )
        plan.save()  
        plan_id = plan.plan_id  
        print(plan_id)
                
        return redirect('see_all_plan')
    
    plans = Plan.objects.all()
    return render(request, 'add_plan.html', {'plans': plans})




@admin_custom_login_required
def update_plan(request, plan_id):
    plan = Plan.objects.get(plan_id=plan_id)
    if request.method == 'POST':
        plan.plan_name = request.POST['plan_name']
        plan.amount = request.POST['amount']
        plan.description = request.POST['description']
        plan.service_no = request.POST['service_no'] 
        plan.save()
        return redirect('see_all_plan')

    return render(request, 'update_plan.html', {'plan': plan})  
@admin_custom_login_required
def admin_delete_plan(request, plan_id):
    plan = Plan.objects.get(plan_id=plan_id)
    if request.method == 'POST':
        plan.delete()
        return redirect('see_all_plan')

    return render(request, 'admin_delete_plan.html', {'plan': plan}) 


from django.shortcuts import render, redirect
from .models import Message

@custom_login_required
def client_message_view(request, fm_id):
    client_id = request.session.get('user_id')

    if request.method == 'POST':
        message_text = request.POST.get('message_text')
        
        # Create a new message entry
        Message.objects.create(
            sender_id=client_id,
            receiver_id=fm_id,  # Fitness manager's ID
            message_text=message_text
        )
        return redirect('send_message', fm_id=fm_id)

    # Fetch conversation history
    messages = (Message.objects.filter(sender_id=client_id, receiver_id=fm_id) | 
               Message.objects.filter(sender_id=fm_id, receiver_id=client_id)).order_by('id')
    
    return render(request, 'client_message.html', {'messages': messages, 'fm_id': fm_id})

@fm_custom_login_required
def view_messages(request):
    fm_id = request.session.get('fm_user_id')  # Get fitness manager's ID from session

    clients = Message.objects.filter(receiver_id=fm_id).values('sender_id').distinct()
    client_details = {client.user_id: client.name for client in Client.objects.filter(user_id__in=[client['sender_id'] for client in clients])}

    context = {
        'clients': client_details.items()  # Pass client IDs and names as a tuple
    }
    return render(request, 'view_messages.html', context)


@fm_custom_login_required
def view_client_messages(request, client_id):
    fm_id = request.session.get('fm_user_id') 

    messages = Message.objects.filter(receiver_id=fm_id, sender_id=client_id).order_by('-id')
    
    client_name = Client.objects.filter(user_id=client_id).values_list('name', flat=True).first()   

    context = {
        'messages': messages,
        'client_id': client_id,
        'client_name': client_name  # Add client name to context
    }
    
    return render(request, 'view_client_messages.html', context)


@fm_custom_login_required
def send_message_to_client(request, client_id):
    fm_id = request.session.get('fm_user_id')  # Get fitness manager's ID from session
    
    if request.method == 'POST':
        message_reply = request.POST.get('message_reply')  # Get the reply message text from the form
        new_message = Message(
            sender_id=client_id,  # Client is still considered the sender
            receiver_id=fm_id,  # Fitness manager is the receiver
            message_reply=message_reply  # Save the message in the message_reply field
        )
        new_message.save()  # Save the new message to the database

        return redirect('view_client_messages', client_id=client_id)

    return HttpResponse(status=405)  # Method Not Allowed if not POST



@fm_custom_login_required
def reply_message(request, message_id):
    if request.method == 'POST':
        reply_text = request.POST.get('reply_text')
        fm_id = request.session.get('fm_user_id')  
        
        try:
            message = Message.objects.get(id=message_id, receiver_id=fm_id)
            message.message_reply = reply_text
            message.save()
            return redirect('view_messages')
        except Message.DoesNotExist:
            return HttpResponse("Message not found or you don't have permission to reply", status=404)
    else:
        return HttpResponse(status=405)
    
from django.db.models import OuterRef, Subquery

@fm_custom_login_required
def nutrition_advice_view(request):
    fm_id = request.session.get('fm_user_id')

    # Get the latest eating habit status for each client
    eating_habit_subquery = EatingHabit2.objects.filter(client_id=OuterRef('client_id')).order_by('-habit_no')

    client_fm_details = ClientFM2.objects.filter(fm_id=fm_id).annotate(
        status=Subquery(eating_habit_subquery.values('status')[:1])
    ).order_by('status', '-id')  # Order by status and then by ID
    
    return render(request, 'nutrition_advice.html', {'client_fm_details': client_fm_details})

@custom_login_required
def eating_habits_view(request):
    client_id = request.session.get('user_id')
    user = Client.objects.get(user_id=client_id)

    user_food_type = user.food_type

    # Get fm_id associated with the user
    fm_relation = ClientFM2.objects.filter(client_id=client_id).first()
    fm_id = fm_relation.fm_id if fm_relation else None

    existing_habits = EatingHabit2.objects.filter(client_id=client_id).values_list('habit_no', flat=True)

    intake_no = request.GET.get('intake', 0)

    veg_habits = EatingHabit.objects.filter(food_type='Vegetarian', intake_no=intake_no).values('habit', 'habit_no','intake_no').distinct()
    non_veg_habits = EatingHabit.objects.filter(food_type='Non-Vegetarian', intake_no=intake_no).values('habit', 'habit_no','intake_no').distinct()

    context = {
        'veg_habits': veg_habits,
        'non_veg_habits': non_veg_habits,
        'user_food_type': user_food_type,
        'fm_id': fm_id,
        'existing_habits': existing_habits,
        'intake_no': intake_no,  # Pass the intake_no to the template for current filter
    }

    if request.method == 'POST':
        selected_habits = request.POST.getlist('selected_habits')
        intake_no = request.POST.get('intake_no')

        selected_habits = [habit for habit in selected_habits if habit]

        for habit_no in selected_habits:
            existing_record = EatingHabit2.objects.filter(client_id=client_id, fm_id=fm_id, intake_no=intake_no, habit_no=habit_no).first()

            if existing_record:
                existing_record.status = 0  # Update other fields as necessary
                existing_record.save()
            else:
                # If it doesn't exist, insert a new record
                EatingHabit2.objects.create(client_id=client_id, fm_id=fm_id, habit_no=habit_no, intake_no=intake_no, status=0)

        messages.success(request, 'Preferences updated successfully.')
        return redirect('personal_nutrition')

    return render(request, 'eating_habits.html', context)







@custom_login_required
def track_foods_view(request):
    client_id = request.session.get('user_id')  # Get the logged-in client ID

    # Get intake_no from GET parameters (default to None if not provided)
    intake_no = request.GET.get('intake_no')

    # Fetch all EatingHabit2 records with status=1 for the logged-in client
    eating_habits = EatingHabit2.objects.filter(client_id=client_id, status=1)

    # Collect all the habit_no's for this client with status=1
    habit_nos = [habit.habit_no for habit in eating_habits]

    # Fetch food items from EatingHabit based on habit_no
    food_details = EatingHabit.objects.filter(habit_no__in=habit_nos)

    # If intake_no is specified, filter food_details based on it
    if intake_no:
        food_details = food_details.filter(intake_no=intake_no)

    return render(request, 'track_foods.html', {'food_details': food_details})



from django.shortcuts import render, redirect
from .models import EatingHabit2, EatingHabit
from django.db.models import Q, OuterRef, Subquery

@fm_custom_login_required
def fm_nutrition_advice(request, client_id):
    fm_id = request.session.get('fm_user_id')

    eating_habits = EatingHabit2.objects.filter(client_id=client_id, fm_id=fm_id, status=0)
    provided=EatingHabit2.objects.filter(client_id=client_id, fm_id=fm_id, status=1)
    client = Client.objects.get(user_id=client_id)
    
    habit_nos = [habit.habit_no for habit in eating_habits]
    food_habits = EatingHabit.objects.filter(habit_no__in=habit_nos)
    provided_habits=EatingHabit.objects.filter(habit_no__in=habit_nos)

    intake_no = request.GET.get('intake_no')
    
    if intake_no:
        food_habits = food_habits.filter(intake_no=intake_no)
        provided_habits=provided_habits.filter(intake_no=intake_no)

    if request.method == 'POST':
        EatingHabit2.objects.filter(client_id=client_id, fm_id=fm_id, status=0).update(status=1)
        messages.success(request, 'Provided the Nutrition successfully')
        return redirect('nutrition_advice')  

    return render(request, 'fm_nutrition_advice.html', {
        'client_id': client_id,
        'food_habits': food_habits,
        'client': client,
        'intake_no': intake_no,  
        'provided_habits':provided_habits
    })





@admin_custom_login_required
def view_feedbacks(request):
    # Query feedbacks and related clients
    feedbacks = Feedback.objects.raw('''
        SELECT f.id, f.content, f.star_rating, c.name 
        FROM tbl_feedback f 
        JOIN client c ON f.user_id = c.user_id
    ''')
    
    # Pass the feedbacks to the template
    context = {
        'feedbacks': feedbacks
    }
    
    return render(request, 'view_feedbacks.html', context)

@fm_custom_login_required
def fm_view_feedbacks(request):
    fm_id = request.session.get('fm_user_id')  # Assuming the fitness manager is logged in with an `fm_id`

    # Query feedbacks for clients associated with this fitness manager
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT f.id, f.content, f.star_rating, c.name 
            FROM tbl_feedback f
            JOIN client c ON f.user_id = c.user_id
            LEFT JOIN tbl_client_fm cf ON c.user_id = cf.client_id AND cf.fm_id = %s
            LEFT JOIN tbl_clientfm2 cf2 ON c.user_id = cf2.client_id AND cf2.fm_id = %s
            LEFT JOIN tbl_mental_fitness mf ON c.user_id = mf.client_id AND mf.fm_id = %s
            WHERE (cf.fm_id IS NOT NULL OR cf2.fm_id IS NOT NULL OR mf.fm_id IS NOT NULL)
        ''', [fm_id, fm_id, fm_id])

        feedbacks = cursor.fetchall()
        feedbacks = [
            {
                'id': row[0],
                'content': row[1],
                'star_rating': row[2],
                'name': row[3],
            }
            for row in feedbacks
        ]

    # Pass the feedbacks to the template
    context = {
        'feedbacks': feedbacks
    }

    return render(request, 'fm_view_feedbacks.html', context)



from django.shortcuts import render, redirect
from .models import Feedback
from django.contrib import messages

@custom_login_required
def feedback(request):
    client_id = request.session.get('user_id')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        star_rating = request.POST.get('star_rating')
        
        if content and star_rating:
            feedback = Feedback(user_id=client_id, content=content, star_rating=int(star_rating))
            feedback.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect('feedback')  # Redirect to the feedback page or any other page
        else:
            messages.error(request, "Please provide both feedback content and a star rating.")
    
    return render(request, 'feedback.html')


@custom_login_required
def mental_fitness(request):
    user_id=request.session.get('user_id')
    client_id = user_id  
    selected_mha = MentalFitness.objects.filter(client_id=client_id).first()

    if not selected_mha:
        messages.error(request, "You have not selected a Mental Helth Advisor yet. Please select to continue.")
        return redirect('select_mha')
    
    context = {
        'mha_selected': selected_mha
    }
    return render(request,'mental_fitness.html',context)

@custom_login_required
def share_thoughts_view(request):
    user_id = request.session.get('user_id')  
    client_id = user_id  

    if request.method == 'POST':
        current_mood = request.POST.get('current_mood')
        
        if current_mood:
            selected_mha = MentalFitness.objects.filter(client_id=client_id).first()

            if selected_mha:
                selected_mha.current_mood = current_mood
                selected_mha.save()

                messages.success(request, 'Your current mood has been updated.')
                return redirect('share_thoughts')  # Stay on the same page to display the reply

    mha_selected = MentalFitness.objects.filter(client_id=client_id).first()

    return render(request, 'share_thoughts.html', {
        'mha_selected': mha_selected 
    })



from django.shortcuts import render, get_object_or_404
from .models import MentalFitness
@fm_custom_login_required
def message_for_thoughts(request, client_id):
    client = get_object_or_404(MentalFitness, client_id=client_id)
    if request.method == 'POST':
        reply = request.POST.get('reply')
        client.distribution = reply
        client.save()
        messages.success(request, 'Your You have replied.')
        return render(request, 'message_for_thoughts.html', {'client': client, 'success': True})
    
    return render(request, 'message_for_thoughts.html', {'client': client})



from django.shortcuts import render
from .models import FitnessManager, MentalFitness, Designations
from django.db.models import Q

@custom_login_required
def select_mha_view(request):
    user_id = request.session.get('user_id')
    if user_id is None:
        messages.error(request, "User not logged in.")
        return redirect('login')  # Redirect to your login page

    client_id = user_id  

    try:
        client = Client.objects.get(user_id=client_id)
    except Client.DoesNotExist:
        messages.error(request, "Client not found.")
        return redirect('login')  # Redirect to an appropriate error page

    if request.method == 'POST':
        mha_id = request.POST.get('mha_id')
        selected_time = request.POST.get('timing')

        if not selected_time:
            messages.error(request, "Timing cannot be empty.")
            return redirect('select_mha')

        # Update or create a new ClientFM record
        selected_mha = MentalFitness.objects.filter(client_id=client_id).first()

        try:
            fitness_manager = FitnessManager.objects.get(user_id=mha_id)
        except FitnessManager.DoesNotExist:
            messages.error(request, "Selected Mental health Advisor does not exist.")
            return redirect('select_mha')

        if selected_mha:
            selected_mha.fm_id = mha_id
            selected_mha.timing = selected_time
            selected_mha.client_name = client.name  # Ensure this field is updated
            selected_mha.fm_name = fitness_manager.name
            selected_mha.status = 0  # Ensure this field is updated
            selected_mha.save()
        else:
            MentalFitness.objects.create(
                client_id=client_id,
                fm_id=mha_id,
                timing=selected_time,
                client_name=client.name, 
                fm_name=fitness_manager.name,
                class_time=datetime.now(),
                status=0
            )
        messages.success(request, 'Selected Mental health Advisor successfully')

        return redirect('mental_fitness')

    # Get fitness managers with designation_id = 2 or 5 and status = 1
    fitness_managers = FitnessManager.objects.filter(
        Q(designation_id=4) | 
        Q(designation_id=4),
        status=1
    )

    # Fetch the designations with id 2 and 5
    designations = Designations.objects.filter(designation_id__in=[4, 4])
    designation_map = {designation.designation_id: designation.designation for designation in designations}

    qualifications = Qualifications.objects.filter(qualification_id__in=[4, 4])
    qualification_map = {qualification.qualification_id: qualification.qualification for qualification in qualifications}

    predefined_times = ['4 AM', '5AM', '9 AM', '8 PM', '9 PM', '10 PM'] 
    
    # Determine assigned times for trainers
    mha_with_details = []
    for mha in fitness_managers:
        assigned_sessions = MentalFitness.objects.filter(fm_id=mha.user_id).values_list('timing', flat=True)
        assigned_times = set(assigned_sessions)  # Convert to set for efficient lookup

        # Filter available times
        available_times = [time for time in predefined_times if time not in assigned_times]

        mha_with_details.append({
            'mha': mha,
            'available_times': available_times,  # Pass available times to the template
            'designation': designation_map.get(mha.designation_id, 'Unknown') ,
             'qualification': qualification_map.get(mha.qualification_id, 'Unknown') 
              # Fetch corresponding designation name
        })

    context = {
        'mha_with_details': mha_with_details,
    }
    return render(request, 'select_mha.html', context)


@custom_login_required 
def view_scheduled_class_mha(request):
    user_id = request.session.get('user_id')

    client_schedule = MentalFitness.objects.filter(client_id=user_id,status=1).first()

    if client_schedule:
        context = {
            'client_schedule': client_schedule,
        }
        return render(request, 'view_scheduled_class_mha.html', context)
    else:
        return render(request, 'view_scheduled_class_mha.html', {'client_schedule': None})

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import MentalFitness, FitnessManager, Client

@fm_custom_login_required
def set_live_mental_session_view(request):
    user_id = request.session.get('fm_user_id')
    clients = Client.objects.all()

    if not user_id:
        messages.error(request, "User not authenticated.")
        return redirect('fm_login')

    try:
        fitness_manager = FitnessManager.objects.get(user_id=user_id)
    except FitnessManager.DoesNotExist:
        messages.error(request, "Fitness Manager does not exist. Please contact support.")
        return redirect('set_live_mental_session')

    if request.method == 'POST':
        class_link = request.POST.get('class_link')
        selected_client_id = request.POST.get('client_id')
        class_time_str = request.POST.get('class_time')
        if class_time_str:
            try:
                class_time_naive = datetime.strptime(class_time_str, '%Y-%m-%dT%H:%M')

                class_time = timezone.make_aware(class_time_naive, timezone.get_current_timezone())

                if class_time < timezone.now():
                    messages.error(request, "Class time cannot be set in the past. Please select a future date and time.")
                    return redirect('set_live_mental_session_view')
            except ValueError:
                messages.error(request, "Invalid date and time format. Please select a valid date and time.")
                return redirect('set_live_mental_session')
        else:
            messages.error(request, "Class time is required.")
            return redirect('set_live_mental_session')
        try:
            mentalfitness = MentalFitness.objects.get(client_id=selected_client_id, fm_id=fitness_manager.user_id)
            mentalfitness.session_link = class_link
            mentalfitness.class_time = class_time
            mentalfitness.status=1
            mentalfitness.save()
            messages.success(request, "Class link updated successfully.")
        except MentalFitness.DoesNotExist:
            messages.error(request, "Client not found or not assigned to you.")
        except ValueError:
            messages.error(request, "Invalid class time format.")
        
        return redirect('set_live_mental_session')

    # Get ClientFM entries for this fitness manager
    clients = MentalFitness.objects.filter(fm_id=fitness_manager.user_id)

    if not clients.exists():
        messages.info(request, "No clients have selected you as their mental health advisor.")

    context = {
        'fitness_manager': fitness_manager,
        'clients': clients,
    }
    return render(request, 'set_live_mental_session.html', context)

@fm_custom_login_required
def join_mental_session(request):
    fm_id = request.session.get('fm_user_id')

    if not fm_id:
        messages.error(request, "User not authenticated.")
        return redirect('fm_login')

    active_sessions = MentalFitness.objects.filter(fm_id=fm_id, status=1)

    context = {
        'active_sessions': active_sessions,
    }

    return render(request, 'join_mental_session.html', context)


from django.shortcuts import render, get_object_or_404


@fm_custom_login_required
def mental_client_details(request, client_id):
    user_id = request.session.get('fm_user_id')
    
    if not user_id:
        messages.error(request, "User not authenticated.")
        return redirect('fm_login')
    
    # Retrieve the client based on the provided client_id
    client = get_object_or_404(Client, user_id=client_id)

    context = {
        'client': client,
    }
    return render(request, 'mental_client_details.html', context)



from django.shortcuts import render, redirect
from .models import Goal
from django.utils import timezone
from django.contrib import messages

from datetime import date

@custom_login_required
def goal(request):
    user_id = request.session.get('user_id')
    user=Client.objects.filter(user_id=user_id).first()
    if user:
        weight=user.weight
        print(weight)
    goal = Goal.objects.filter(user_id=user_id).first()

    if goal and goal.end_date:
        today = date.today()
        remaining_days = (goal.end_date - today).days
    else:
        remaining_days = None

    return render(request, 'goal.html', {'goal': goal, 'remaining_days': remaining_days,'weight': weight})


from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from .models import Goal  # Ensure the Goal model is correctly imported
from datetime import datetime

@custom_login_required
def set_goal(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user = Client.objects.filter(user_id=user_id).first()
        
        if user:
            weight = user.weight
            target_value = int(request.POST['target_value'])
            target_type = request.POST['target_type']

        # Check if a goal already exists for the user
        existing_goal = Goal.objects.filter(user_id=user_id).first()
        
        
        if existing_goal:
            messages.error(request, 'You have already set a goal.')
            return redirect('goal')  # Redirect back to the goal page

        # Validate that the target value is within ±30 kg of the starting value
        if abs(target_value - weight) > 30:
            messages.error(request, 'Target value must be within ±30 kg of the starting value.')
            return redirect('set_goal')

        # Validate that the target value is not less than the starting value for specific target types
        if target_type in ["weight gain", "muscle gain", "bulking"] and target_value < weight:
            messages.error(request, f'Target value for {target_type} should not be less than the starting value.')
            return redirect('set_goal')
        if target_type in ["weight loss", "cutting"] and target_value > weight:
            messages.error(request, f'Target value for {target_type} should not be greater than the starting value.')
            return redirect('set_goal')

        # Validate that the start date is not in the past
        start_date_str = request.POST['start_date']
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if start_date < timezone.now().date():
            messages.error(request, 'Start date cannot be in the past.')
            return redirect('set_goal')

        # Create a new goal since no existing goal was found and validation passed
        Goal.objects.create(
            target_type=target_type,
            starting_value=weight,
            target_value=target_value,
            current_value=weight,  # Initially set current_value to starting_value
            user_id=user_id,
            no_of_days=request.POST['no_of_days'],
            description=request.POST['description'],
            start_date=start_date,
            end_date=timezone.now() + timezone.timedelta(days=int(request.POST['no_of_days']))
        )

        messages.success(request, 'Goal set successfully.')
        return redirect('goal')  # Redirect to the goal page after successful creation

    return redirect('goal')  # Redirect to the goal page for non-POST requests


@custom_login_required
def update_goal(request, goal_id):
    user_id = request.session.get('user_id')
    user=Client.objects.filter(user_id=user_id).first()
    if user:
        weight=user.weight
        print(weight)
    if request.method == 'POST':
        goal = Goal.objects.get(id=goal_id)
        goal.current_value = int(request.POST['current_value'])
        goal.target_value = int(request.POST['target_value'])
        goal.no_of_days = request.POST['no_of_days']
        if goal.target_type in ["weight gain", "muscle gain", "bulking"]:
            if goal.target_value < goal.starting_value:
                messages.error(request, 'For weight gain, muscle gain, or bulking, the target value must not be less than the starting value.')
                return redirect('goal')

        elif goal.target_type in ["weight loss", "cutting"]:
            if goal.target_value > goal.starting_value:
                messages.error(request, 'For weight loss or cutting, the target value must not be greater than the starting value.')
                return redirect('goal')
        goal.save()
        user.weight=goal.current_value
        user.save()
        print(user.weight)
        messages.success(request, 'Goal updated successfully.')
    return redirect('goal')


@custom_login_required
def delete_goal(request, goal_id):
    goal = Goal.objects.get(id=goal_id)
    goal.delete()
    messages.success(request, 'Goal deleted successfully.')
    return redirect('goal')

@custom_login_required
def progress(request):
    user_id = request.session.get('user_id')
    user=Client.objects.filter(user_id=user_id).first()
    if user:
        weight=user.weight
        height=user.height
        print(weight)

    # Fetch all progress records for the user
    progress_records = Progress.objects.filter(user_id=user_id).order_by('-current_bmi_date')

    # Initialize starting_bmi
    starting_bmi = None

    # Check if there are any records for the user
    if progress_records.exists():
        starting_bmi = progress_records.first().starting_bmi  # Get the starting BMI from the first record

    if request.method == 'POST':
        try:
            height =height
            weight = weight
            current_bmi_date = request.POST.get('current_bmi_date')

            if timezone.datetime.strptime(current_bmi_date, '%Y-%m-%d').date() < timezone.now().date():
                messages.error(request, 'Date cannot be in the past.')
                return redirect('progress')

        # Check if the date has already been selected (Assuming you have a model for Progress)
            existing_progress = Progress.objects.filter(current_bmi_date=current_bmi_date, user_id=user_id)
            if existing_progress.exists():
                messages.error(request, 'You have already selected this date for BMI tracking.')
                return redirect('progress')

            height_in_meters = height / 100
            current_bmi = (weight / height_in_meters ** 2)

            # Check if a record already exists for the date
            if not Progress.objects.filter(user_id=user_id, current_bmi_date=current_bmi_date).exists():
                # If no starting BMI has been set, use the current BMI as the starting BMI
                if starting_bmi is None:
                    starting_bmi = current_bmi
                
                Progress.objects.create(
                    user_id=user_id,
                    starting_bmi=starting_bmi,
                    current_bmi=current_bmi,
                    current_bmi_date=current_bmi_date,
                    target_bmi='18.5 to 24.9'  # Set a target BMI if required
                )
                return redirect('progress')  # Refresh the page after saving
            else:
                # Handle case where the record already exists
                print(f"Record already exists for date: {current_bmi_date}")
                # Set an error message to show to the user

        except (ValueError, TypeError) as e:
            print(f"Error in BMI calculation: {e}")
            # Set an error message to show to the user

    # Prepare data for the chart
    bmi_dates = [record.current_bmi_date for record in progress_records]
    starting_bmis = [record.starting_bmi for record in progress_records]
    current_bmis = [record.current_bmi for record in progress_records]

    context = {
        'starting_bmi': starting_bmi,  # Use the starting BMI calculated above
        'target_bmi': '18.5 to 24.9',  # Update based on your logic
        'current_bmi': progress_records.first().current_bmi if progress_records else None,
        'current_bmi_date': progress_records.first().current_bmi_date if progress_records else None,
        'bmi_dates': bmi_dates,
        'starting_bmis': starting_bmis,
        'current_bmis': current_bmis,
        'height': height,
        'weight' : weight,
    }

    return render(request, 'progress.html', context)


from django.http import JsonResponse
from django.utils.dateparse import parse_date

@custom_login_required
def get_bmi_data(request, selected_date):
    user_id = request.session.get('user_id')
    # Ensure the date format is parsed correctly
    selected_date = parse_date(selected_date)
    
    try:
        progress_record = Progress.objects.get(user_id=user_id, current_bmi_date=selected_date)
        data = {
            'starting_bmi': progress_record.starting_bmi,
            'current_bmi': progress_record.current_bmi,
            'target_bmi': '18.5 to 24.9'  # Update based on your logic
        }
        return JsonResponse(data)
    except Progress.DoesNotExist:
        return JsonResponse({'starting_bmi': None, 'current_bmi': None, 'target_bmi': '18.5 to 24.9'})


@custom_login_required
def goal_progress(request):
    user_id = request.session.get('user_id')

    # Fetch the goal record for the user
    try:
        goal = Goal.objects.get(user_id=user_id)
    except Goal.DoesNotExist:
        # Handle case where no goal is found for the user
        messages.error(request, 'No goal found for your account.')
        return redirect('goal')  # Redirect to a suitable view

    context = {
        'goal': goal,
    }

    return render(request, 'goal_progress.html', context)



@fm_custom_login_required
def view_goal_progress(request, client_id, goal_id):
    user_id = request.session.get('fm_user_id')
    
    if not user_id:
        messages.error(request, "User not authenticated.")
        return redirect('fm_login')

    # Retrieve the goal based on the provided goal_id
    goal = get_object_or_404(Goal, id=goal_id, user_id=client_id)

    context = {
        'goal': goal,
    }
    return render(request, 'view_goal_progress.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import FMSkills
from django.core.files.storage import FileSystemStorage

@fm_custom_login_required
def fm_skills_view(request):
    fm_id = request.session.get('fm_user_id')

    # Check if FMSkills already exists for the logged-in Fitness Manager
    try:
        fm_skills = FMSkills.objects.get(fm_id=fm_id)
    except FMSkills.DoesNotExist:
        fm_skills = None

    if request.method == 'POST':
        # Handle form submission for either insert or update
        skills = request.POST.get('skills')
        achievements = request.POST.get('achievements')
        gym_pic = request.FILES.get('gym_pic')
        achievement_proof = request.FILES.get('achievement_proof')

        # Create or update the FMSkills instance
        if fm_skills:
            # Update existing record
            fm_skills.skills = skills
            fm_skills.achievements = achievements
            if gym_pic:
                fm_skills.gym_pic = gym_pic
            if achievement_proof:
                fm_skills.achievement_proof = achievement_proof
            fm_skills.save()
            messages.success(request, 'Your skills and achievements have been updated.')
        else:
            # Create new record
            new_fm_skill = FMSkills(
                fm_id=fm_id,
                skills=skills,
                achievements=achievements
            )
            if gym_pic:
                new_fm_skill.gym_pic = gym_pic
            if achievement_proof:
                new_fm_skill.achievement_proof = achievement_proof
            new_fm_skill.save()
            messages.success(request, 'Your skills and achievements have been added.')

        return redirect('fm_skills')

    return render(request, 'fm_skills.html', {'fm_skills': fm_skills})



from django.shortcuts import render
from .models import FitnessManager, Designations

@fm_custom_login_required
def fm_header(request):
    fm_id = request.session.get('fm_user_id')
    print(fm_id)
    
    fitness_manager = FitnessManager.objects.filter(user_id=fm_id).first()
    designation_id = fitness_manager.designation_id if fitness_manager else None
    print(designation_id)
    
    workout_trainer = designation_id in [2, 5]
    dietitian = designation_id == 3
    mental_fm = designation_id == 4

    return render(request, 'fm_header.html', {
        'workout_trainer': workout_trainer,
        'dietitian': dietitian,
        'mental_fm': mental_fm
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Product, Order

# Admin views for managing the shop
from django.db.models import Q

from django.db import connection
@admin_custom_login_required
def admin_shop(request):
    query = request.GET.get('search', '')  # Get the search query from the request
    selected_category = request.GET.get('category', '')  # Get the selected category ID
    
    # Fetch all categories from the database
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM app_category")
        categories = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    
    # Filter products based on search query and selected category
    products = Product.objects.all()
    if query:
        products = products.filter(name__icontains=query)
    if selected_category:
        products = products.filter(category_id=selected_category)
    
    # Map category IDs to category names
    category_map = {category['id']: category['name'] for category in categories}
    for product in products:
        product.category_name = category_map.get(product.category_id, "Unknown")
    
    return render(request, 'admin_shop.html', {
        'products': products,
        'query': query,
        'categories': categories,
        'selected_category': selected_category
    })
from django.db import connection
from django.shortcuts import render
from .models import Product
@admin_custom_login_required
def stock_management(request):
    query = request.GET.get('search', '').strip()
    selected_category = request.GET.get('category', '').strip()

    # Get all categories for the dropdown
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM app_category")
        categories = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

    # Filter products based on search and category
    products = Product.objects.all()
    if query:
        products = products.filter(name__icontains=query)
    if selected_category:
        products = products.filter(category_id=selected_category)

    # Find products with stock 2 or less
    low_stock_products = products.filter(stock__lte=2)

    # Map category names to products
    category_map = {category['id']: category['name'] for category in categories}
    for product in products:
        product.category_name = category_map.get(product.category_id, "Unknown")

    return render(request, 'stock_management.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': selected_category,
        'low_stock_products': low_stock_products,
    })




from django.db import connection
@admin_custom_login_required
def add_product(request):
    if request.method == "POST":
        name = request.POST['name']
        description = request.POST['description']
        price = request.POST['price']
        stock = request.POST['stock']
        category_id = request.POST['category']
        image = request.FILES.get('image')

        # Save the product with the selected category ID
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category_id=category_id,
            image=image
        )
        product.save()

        return redirect('admin_shop')

    # Fetch all categories for the dropdown
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM app_category")
        categories = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    return render(request, 'add_product.html', {'categories': categories})


from django.db import connection
@admin_custom_login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Fetch all categories for display
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM app_category")
        categories = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    if request.method == "POST":
        product.name = request.POST['name']
        product.description = request.POST['description']
        product.price = request.POST['price']
        product.stock = request.POST['stock']
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        return redirect('admin_shop')

    return render(request, 'edit_product.html', {'product': product, 'categories': categories})

@admin_custom_login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('admin_shop')
@admin_custom_login_required
def manage_orders(request):
    orders = Order.objects.select_related('product').all()
    return render(request, 'manage_orders.html', {'orders': orders})

# views.py
from django.shortcuts import render, get_object_or_404
from .models import Product, Category
from django.db.models import Q


@custom_login_required
def shop_home(request):
    user_id = request.session.get('user_id')
    print(user_id)
    
    # Fetch categories and products
    categories = Category.objects.all()
    products = Product.objects.all()

    # Search functionality
    query = request.GET.get('query', '')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # Filter by category
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)

    # Fetch wishlist items for the user
    wishlist_items = Wishlist.objects.filter(user_id=user_id).values_list('product_id', flat=True)

    context = {
        'categories': categories,
        'products': products,
        'wishlist_items': wishlist_items,  # Pass wishlist product IDs to the template
    }
    return render(request, 'shop.html', context)


# Product details page
@custom_login_required
def product_detail(request, product_id):
    user_id = request.session.get('user_id')
    print(user_id)
    product = get_object_or_404(Product, id=product_id)
    wishlist_items = Wishlist.objects.filter(user_id=user_id).values_list('product_id', flat=True)

    return render(request, 'product_detail.html', {'product': product,'wishlist_items': wishlist_items})


from django.http import JsonResponse
from transformers import pipeline
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.db.models import Q

# Load the pre-trained NLP model for feature extraction
nlp_model = pipeline("feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2")

BODY_PART_SYNONYMS = {
    "hand": ["wrist", "arm", "fingers", "grip"],
    "leg": ["thigh", "calf", "foot", "ankle"],
    "shoulder": ["arm", "neck", "upper body"],
    "back": ["spine", "posture", "lower back", "pull up bar"],
    "chest": ["pecs", "pectorals", "upper body", "push up"],
    "weight loss": ["fat burn", "slimming", "cardio"],
    "muscle gain": ["bodybuilding", "strength training", "mass gain"],
    # Add more terms as needed
}

def expand_query(query):
    """Expand the query using synonyms if found."""
    expanded_terms = BODY_PART_SYNONYMS.get(query.lower(), [])
    return [query] + expanded_terms

@custom_login_required
def search_products(request):
    
    query = request.GET.get('query', '').strip()
    
    if not query:
        return JsonResponse({'products': []})

    # Expand the query using synonyms
    expanded_queries = expand_query(query)
    
    # Fetch all products using substring search
    substring_matches = Product.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )[:10]  # Limit the results for performance

    # Fetch all products for semantic similarity search
    products = Product.objects.all()
    product_descriptions = [product.description for product in products]

    # Encode the query and product descriptions into vectors
    query_vectors = [np.mean(nlp_model(q), axis=1) for q in expanded_queries]
    product_vectors = [np.mean(nlp_model(desc), axis=1) for desc in product_descriptions if desc]

    # Compute cosine similarity between each query vector and product vectors
    similarities = [
        max(cosine_similarity(query_vector, pv)[0][0] for query_vector in query_vectors)
        for pv in product_vectors
    ]

    # Rank products by similarity score
    ranked_products = sorted(
        zip(products, similarities), 
        key=lambda x: x[1], 
        reverse=True
    )

    # Filter products with a similarity score above a threshold
    semantic_matches = [prod for prod, score in ranked_products if score > 0.5][:10]  # Limit to top 10

    # Combine substring matches and semantic matches, ensuring no duplicates
    combined_results = list(set(substring_matches) | set(semantic_matches))

    # Prepare the data to send back
    results = [{
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': str(product.price),  # Convert Decimal to string for JSON
        'image': product.image.url if product.image else None,
    } for product in combined_results]

    return JsonResponse({'products': results})


# Filter products by category
@custom_login_required
def filter_products(request):
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    products = Product.objects.all()

    if category:
        products = products.filter(category_id=category)
    
    if min_price:
        products = products.filter(price__gte=float(min_price))
    
    if max_price:
        products = products.filter(price__lte=float(max_price))

    # Get wishlist items for the current user
    wishlist_items = []
    if 'user_id' in request.session:
        wishlist_items = Wishlist.objects.filter(
            user_id=request.session['user_id']
        ).values_list('product_id', flat=True)

    context = {
        'products': products,
        'wishlist_items': wishlist_items,
        'categories': Category.objects.all()
    }
    
    return render(request, 'shop.html', context)

from django.views.decorators.csrf import csrf_exempt  # Required for AJAX requests if CSRF token is missing

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Cart

@csrf_exempt  # Remove this if you handle CSRF tokens in the frontend
@custom_login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)  # Parse JSON body
        quantity = data.get('quantity', 1)  # Default quantity is 1
        user_id = request.session.get('user_id')  # Assuming user_id is stored in session
        
        # Check if the item is already in the cart
        cart_item, created = Cart.objects.get_or_create(user_id=user_id, product_id=product_id)
        if not created:
            # If the item is already in the cart, update the quantity
            # cart_item.quantity += quantity
            # cart_item.save()
            message = 'Item already in the cart.Please check your cart.'
        else:
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Item added to cart successfully!'
        
        return JsonResponse({'message': message})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

from django.shortcuts import render, redirect
from .models import Cart

@custom_login_required
def cart_view(request):
    user_id = request.session.get('user_id')  # Assuming user_id is stored in session
    cart_items = Cart.objects.filter(user_id=user_id,status=0)
    # Handle the POST request to update cart quantities
    if request.method == 'POST':
        for item in cart_items:
            # Get the new quantity from the form
            new_quantity = request.POST.get(f'quantity_{item.id}')
            if new_quantity:
                new_quantity = int(new_quantity)  # Convert to integer
                if new_quantity != item.quantity:
                    item.quantity = new_quantity  # Update quantity
                    item.save()  # Save the updated item to the database

        # Redirect to the same cart page after updating
        return redirect('cart_view')

    # Calculate total cart value (reflecting updated quantities)
    total_price = sum(item.quantity * item.product.price for item in cart_items)

    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})


@custom_login_required
def remove_from_cart(request, item_id):
    cart_item = Cart.objects.get(id=item_id)
    cart_item.delete()  # Delete the item from the cart

    return redirect('cart_view')


from django.shortcuts import render
from .models import Order, Address  # Replace `myapp` with your actual app name

@custom_login_required
def order_view(request):
    user_id = request.session.get('user_id')  # Assuming session contains user ID
    orders = Order.objects.filter(
        user_id=user_id, 
    ).select_related('address', 'product').order_by('-order_date')
    
    # Calculate if order is still cancellable (within 2 days of payment)
    for order in orders:
        order.can_cancel = (
            order.status == 'Paid' and 
            timezone.now() - order.order_date <= timedelta(days=2)
        )
    
    return render(request, 'order.html', {'orders': orders})

@custom_login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Check if order is within cancellation window (2 days)
    if timezone.now() - order.order_date <= timedelta(days=2) and order.status == 'Paid':
        order.status = 'Cancelled'
        order.save()
        
        # Restore product stock
        product = order.product
        product.stock += order.quantity
        product.save()
        
        messages.success(request, 'Order cancelled successfully')
    else:
        messages.error(request, 'Order cannot be cancelled after 2 days of payment')
    
    return render(request, 'order.html')


import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Order, Payment

# Razorpay client initialization    
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@custom_login_required
def initiate_payment(request):
    user_id = request.session.get('user_id')
    address_id = request.session.get('address_id')
    
    if not address_id:
        messages.error(request, "Please confirm your delivery address first")
        return redirect('address_confirmation')
        
    cart_items = Cart.objects.filter(user_id=user_id, status=0)

    if not cart_items:
        return redirect('cart')

    # Calculate total amount for all items
    total_amount = sum(item.total_price for item in cart_items)

    # Create Razorpay order
    razorpay_order = razorpay_client.order.create({
        "amount": int(total_amount * 100),
        "currency": "INR",
        "payment_capture": "1"
    })

    # Create orders for each cart item
    orders = []
    for cart_item in cart_items:
        order = Order.objects.create(
            user_id=user_id,
            product=cart_item.product,
            quantity=cart_item.quantity,
            total_price=cart_item.total_price,
            address_id=address_id  # Use the address_id from session
        )
        orders.append(order)

    # Create payment record
    payment = Shop_Payment.objects.create(
        user_id=user_id,
        order=orders[0],
        razorpay_order_id=razorpay_order['id'],
        amount=total_amount,
    )

    # Update cart status and product stock
    if razorpay_order:
        for cart_item in cart_items:
            product = cart_item.product
            if product.stock >= cart_item.quantity:
                product.stock -= cart_item.quantity
                product.save()
            else:
                # Rollback orders if stock is insufficient
                for order in orders:
                    order.delete()
                return redirect('cart')

            cart_item.status = 1
            cart_item.save()

    context = {
        "orders": orders,
        "payment": payment,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "razorpay_order_id": razorpay_order['id'],
        "amount": total_amount,
        "currency": "INR",
    }
    return render(request, 'payment.html', context)


from django.shortcuts import render, redirect
from .models import Address, Cart

@custom_login_required
def address_confirmation(request):
    user_id = request.session.get('user_id')
    
    # Get cart items and total price for order summary
    with connection.cursor() as cursor:
        # Get cart items
        cursor.execute("""
            SELECT c.id, c.quantity, p.name, p.price, (c.quantity * p.price) as total_price
            FROM app_cart c
            JOIN app_product p ON c.product_id = p.id
            WHERE c.user_id = %s AND c.status = 0
        """, [user_id])
        cart_items = dictfetchall(cursor)
        
        # Calculate total price
        total_price = sum(item['total_price'] for item in cart_items)
        
        # Get existing address if any
        cursor.execute("""
            SELECT * FROM app_address 
            WHERE user_id = %s
        """, [user_id])
        address = dictfetchall(cursor)
        address = address[0] if address else None

    if request.method == "POST":
        # Get coordinates for the ZIP code instead of using client's location
        zip_code = request.POST.get("zip_code")
        latitude, longitude = get_pincode_coordinates(zip_code)
        
        with connection.cursor() as cursor:
            if address:
                # Update existing address
                cursor.execute("""
                    UPDATE app_address 
                    SET address_line1 = %s,
                        city = %s,
                        state = %s,
                        zip_code = %s,
                        contact_number = %s,
                        delivery_latitude = %s,
                        delivery_longitude = %s
                    WHERE user_id = %s
                """, [
                    request.POST.get("address_line1"),
                    request.POST.get("city"),
                    request.POST.get("state"),
                    zip_code,
                    request.POST.get("contact_number"),
                    latitude,  # Using ZIP code coordinates
                    longitude, # Using ZIP code coordinates
                    user_id
                ])
                # Get the address ID
                cursor.execute("SELECT id FROM app_address WHERE user_id = %s", [user_id])
                address_id = cursor.fetchone()[0]
            else:
                # Create new address
                cursor.execute("""
                    INSERT INTO app_address 
                    (user_id, address_line1, city, state, zip_code, contact_number, delivery_latitude, delivery_longitude)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    user_id,
                    request.POST.get("address_line1"),
                    request.POST.get("city"),
                    request.POST.get("state"),
                    zip_code,
                    request.POST.get("contact_number"),
                    latitude,  # Using ZIP code coordinates
                    longitude  # Using ZIP code coordinates
                ])
                # Get the last inserted ID
                cursor.execute("SELECT LAST_INSERT_ID()")
                address_id = cursor.fetchone()[0]
            
            # Store address_id in session
            request.session['address_id'] = address_id
        
        return redirect('initiate_payment')
    
    # For GET request, render the form
    context = {
        'address': address,
        'cart_items': cart_items,
        'total_price': total_price
    }
    return render(request, 'address_confirmation.html', context)

@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        data = request.POST
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        payment = get_object_or_404(Shop_Payment, razorpay_order_id=razorpay_order_id)

        try:
            # Verify the payment signature
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # Update payment details
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = 'Completed'
            payment.save()

            # Get reference time from the first order
            reference_time = payment.order.order_date
            
            # Create a time window of 1 minute before and after
            time_window_start = reference_time - timezone.timedelta(minutes=1)
            time_window_end = reference_time + timezone.timedelta(minutes=1)

            # Update all orders for this user within the time window
            Order.objects.filter(
                user_id=payment.user_id,
                order_date__range=(time_window_start, time_window_end)
            ).update(status='Paid')

            # After order status is updated to 'Paid'
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE app_order o
                    JOIN app_address a ON o.address_id = a.id
                    SET o.status = 'Paid',
                        o.delivery_center = %s
                    WHERE o.id = %s
                """, [get_nearest_center(payment.order.address.zip_code), payment.order.id])

            return redirect('payment_success')
            
        except razorpay.errors.SignatureVerificationError:
            print("Payment verification failed.")
            print("Razorpay Order ID:", razorpay_order_id)
            print("Razorpay Payment ID:", razorpay_payment_id)
            print("Razorpay Signature:", razorpay_signature)

            payment.status = 'Failed'
            payment.save()
            return redirect('payment_failed')

def payment_success(request):
    return render(request, 'Shop_payment_success.html')
def payment_failed(request):
    return render(request, 'shop_payment_failed.html')

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Product, Wishlist
@custom_login_required
def add_to_wishlist(request, product_id):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        product = get_object_or_404(Product, id=product_id)

        # Check if the item is already in the wishlist
        existing_item = Wishlist.objects.filter(user_id=user_id, product=product).first()
        if existing_item:
            return JsonResponse({
                "success": False,
                "message": "Item already in wishlist"
            }, status=400)

        # Add item to wishlist
        Wishlist.objects.create(user_id=user_id, product=product)
        return JsonResponse({
            "success": True,
            "message": "Item added to wishlist successfully"
        })

    return JsonResponse({
        "success": False,
        "message": "Invalid request method"
    }, status=405)
@custom_login_required
def view_wishlist(request):
    user_id = request.session.get('user_id')  # Assuming user authentication
    wishlist_items = Wishlist.objects.filter(user_id=user_id).select_related('product')
    context = {
        'wishlist_items': wishlist_items
    }
    return render(request, 'wishlist.html', context)
@custom_login_required
def remove_from_wishlist(request, wishlist_id):
    try:
        wishlist_item = Wishlist.objects.get(
            product_id=wishlist_id, 
            user_id=request.session.get('user_id')
        )
        wishlist_item.delete()
        return JsonResponse({
            "success": True,
            "message": "Item removed from wishlist"
        })
    except Wishlist.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Item not found in wishlist"
        }, status=404)

from django.shortcuts import render
from .utils.mind_body_synergy import multi_output_model, encoder_dict, scaler
import pandas as pd
@custom_login_required
def predict_fitness(request):
    if request.method == 'POST':
        # Get form data
        exercise_hours = float(request.POST.get('exercise_hours_per_week', 0))
        sleep_hours = float(request.POST.get('sleep_hours_per_night', 0))
        physical_fitness_level = request.POST.get('physical_fitness_level')
        diet_quality = request.POST.get('diet_quality')
        user_id = request.session.get('user_id')

        # Server-side validation
        if not (0 <= exercise_hours <= 15 and 0 <= sleep_hours <= 15):
            messages.error(request, 'Exercise and sleep hours must be between 0 and 15')
            return redirect('predict_fitness')

        # Extract user inputs from the form
        user_data = {
            'Physical_Fitness_Level': physical_fitness_level,
            'Exercise_Hours_Per_Week': exercise_hours,
            'Sleep_Hours_Per_Night': sleep_hours,
            'Diet_Quality': diet_quality,
        }

        # Convert to DataFrame
        input_data = pd.DataFrame([user_data])

        # Encode categorical columns
        for col in ["Physical_Fitness_Level", "Diet_Quality"]:
            encoder = encoder_dict.get(col)
            if encoder:
                input_data[col] = input_data[col].apply(
                    lambda x: encoder.transform([x])[0] if x in encoder.classes_ else -1
                )

        # Scale the data
        input_data_scaled = scaler.transform(input_data)

        # Predict outcomes
        predictions = multi_output_model.predict(input_data_scaled)

        # Decode categorical predictions where applicable
        predictions_df = pd.DataFrame(predictions, columns=[
            "Mental_Fitness_Level", "Stress_Level", "Social_Engagement_Score",
            "Depression_Score", "Anxiety_Score", "Confidence_Level", "Cleverness_Score", "Focus_Level"
        ])

        def decode_column(col, value):
            encoder = encoder_dict.get(col)
            return encoder.inverse_transform([int(round(value))])[0] if encoder else value

        # Convert categorical values
        for col in ["Mental_Fitness_Level", "Stress_Level", "Confidence_Level", "Focus_Level"]:
            predictions_df[col] = predictions_df[col].apply(lambda x: decode_column(col, x))

        # Convert numeric scores to percentages
        numeric_columns = [
            "Social_Engagement_Score", 
            "Depression_Score", 
            "Anxiety_Score", 
            "Cleverness_Score"
        ]
        
        for col in numeric_columns:
            predictions_df[col] = predictions_df[col].apply(lambda x: f"{round(x * 10)}%")

        # Get the predictions as a dictionary
        prediction_results = predictions_df.iloc[0].to_dict()

        # Store the predictions in the database
        with connection.cursor() as cursor:
            # Convert percentage strings back to float values for storage
            social_score = float(prediction_results['Social_Engagement_Score'].rstrip('%')) / 10
            depression_score = float(prediction_results['Depression_Score'].rstrip('%')) / 10
            anxiety_score = float(prediction_results['Anxiety_Score'].rstrip('%')) / 10
            cleverness_score = float(prediction_results['Cleverness_Score'].rstrip('%')) / 10

            cursor.execute("""
                INSERT INTO tbl_mental_fitness_predictions 
                (user_id, physical_fitness_level, exercise_hours, sleep_hours, diet_quality,
                mental_fitness_level, stress_level, social_engagement_score, depression_score,
                anxiety_score, confidence_level, cleverness_score, focus_level)
                VALUES 
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                user_id, 
                physical_fitness_level, 
                exercise_hours, 
                sleep_hours, 
                diet_quality,
                prediction_results['Mental_Fitness_Level'],
                prediction_results['Stress_Level'],
                social_score,
                depression_score,
                anxiety_score,
                prediction_results['Confidence_Level'],
                cleverness_score,
                prediction_results['Focus_Level']
            ])

        # Render results
        return render(request, 'predict_results.html', {
            'predictions': prediction_results,
        })

    # For GET request, calculate pre-filled values
    user_id = request.session.get('user_id')
    current_date = datetime.now().date()

    # Get the most recent week's data
    with connection.cursor() as cursor:
        # Get the most recent week_start_date from either completion table
        cursor.execute("""
            SELECT week_start_date 
            FROM (
                SELECT week_start_date FROM WeeklyWorkoutCompletion 
                WHERE client_id = %s
                UNION
                SELECT week_start_date FROM WeeklyNutritionCompletion 
                WHERE client_id = %s
            ) combined_dates
            ORDER BY week_start_date DESC
            LIMIT 1
        """, [user_id, user_id])
        
        result = cursor.fetchone()
        if result:
            week_start_date = result[0]
            
            # Count completed workouts for the week
            cursor.execute("""
                SELECT COUNT(*) 
                FROM WeeklyWorkoutCompletion 
                WHERE client_id = %s AND week_start_date = %s
            """, [user_id, week_start_date])
            workout_count = cursor.fetchone()[0]
            
            # Calculate exercise hours (divide total workouts by 9 to get hours)
            exercise_hours = min(workout_count / 9, 15)  # Cap at 15 hours
            
            # Determine physical fitness level based on workout completion
            if workout_count >= 10:
                physical_fitness = "High"
            elif workout_count >= 5:
                physical_fitness = "Medium"
            else:
                physical_fitness = "Low"
            
            # Count completed nutrition days for the week
            cursor.execute("""
                SELECT COUNT(DISTINCT nutrition_id) 
                FROM WeeklyNutritionCompletion 
                WHERE client_id = %s AND week_start_date = %s
            """, [user_id, week_start_date])
            nutrition_days = cursor.fetchone()[0]
            
            # Determine diet quality based on nutrition completion
            if nutrition_days >= 6:
                diet_quality = "Good"
            elif nutrition_days >= 3:
                diet_quality = "Average"
            else:
                diet_quality = "Poor"
        else:
            # Default values if no data is found
            exercise_hours = 0
            physical_fitness = "Low"
            diet_quality = "Average"

        # Get historical prediction data
        cursor.execute("""
            SELECT 
                DATE_FORMAT(prediction_date, '%%Y-%%m-%%d') as prediction_date,
                mental_fitness_level, 
                stress_level, 
                social_engagement_score * 10 as social_engagement_score, 
                depression_score * 10 as depression_score,
                anxiety_score * 10 as anxiety_score,
                confidence_level,
                cleverness_score * 10 as cleverness_score,
                focus_level
            FROM tbl_mental_fitness_predictions
            WHERE user_id = %s
            ORDER BY prediction_date DESC
            LIMIT 5
        """, [user_id])
        
        columns = [col[0] for col in cursor.description]
        historical_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    context = {
        'prefilled_data': {
            'exercise_hours': round(exercise_hours, 1),  # Round to 1 decimal place
            'physical_fitness': physical_fitness,
            'diet_quality': diet_quality
        },
        'historical_data': json.dumps(historical_data, cls=DjangoJSONEncoder)
    }
    
    return render(request, 'predict_form.html', context)
    
from django.shortcuts import render
from .models import Client
from .utils.injury_predictor import predict_injury
from .decorators import custom_login_required

@custom_login_required
def injury_prediction_view(request):
    user_id = request.session.get("user_id")

    try:
        client = Client.objects.get(user_id=user_id)
        player_age = client.age
        player_weight = client.weight
        player_height = client.height
        gender = client.gender
    except Client.DoesNotExist:
        return render(request, "injury_prediction.html", {"message": "Client not found."})

    # Initialize default values for context
    is_pregnant = 0
    previous_injuries = 0
    disease_status = 0
    diseases = []
    injury_type = "Other"

    if request.method == "POST":
        # Extract form data
        previous_injuries = int(request.POST["previous_injuries"])
        is_pregnant = int(request.POST.get("is_pregnant", 0)) if gender.lower() == "female" else 0
        disease_status = int(request.POST["disease_status"])
        diseases = request.POST.get("disease_details", "").split(",") if disease_status == 1 else []
        injury_type = request.POST["injury_type"]

        # Prepare input for model
        input_data = [
            player_age, player_weight, player_height, previous_injuries,
            gender, is_pregnant, disease_status, len(diseases), injury_type
        ]

        # Predict outcomes
        prediction = predict_injury(input_data)
        training_intensity, likelihood_of_injury, recovery_time = prediction

        context = {
            "training_intensity": training_intensity,
            "likelihood_of_injury": likelihood_of_injury,
            "recovery_time": recovery_time,
            "form_data": input_data,
            "injury_type": injury_type
        }
        return render(request, "injury_result.html", context)

    # Default context for GET request
    context = {
        "player_age": player_age,
        "player_weight": player_weight,
        "player_height": player_height,
        "gender": gender,
        "is_pregnant": is_pregnant,
        "previous_injuries": previous_injuries,
        "disease_status": disease_status,
        "diseases": diseases,
        "injury_type": injury_type,
    }
    return render(request, "injury_prediction.html", context)

@custom_login_required
def analyze_workout_view(request):
    if request.method == 'POST' and request.FILES.get('workout_video'):
        video_file = request.FILES['workout_video']
        
        # Validate file type
        if not video_file.content_type.startswith('video/'):
            messages.error(request, "Please upload a valid video file.")
            return render(request, 'analyze_workout.html')

        # Validate file size (e.g., max 50MB)
        if video_file.size > 50 * 1024 * 1024:
            messages.error(request, "Video file is too large. Maximum size is 50MB.")
            return render(request, 'analyze_workout.html')

        try:
            fs = FileSystemStorage()
            # Create directory if it doesn't exist
            os.makedirs('media/workout_videos', exist_ok=True)
            filename = fs.save(f'workout_videos/{video_file.name}', video_file)
            video_path = fs.path(filename)

            # Analyze the video
            analyzer = WorkoutAnalyzer()
            analysis_results = analyzer.analyze_form(video_path)

            # Clean up the uploaded file
            if os.path.exists(video_path):
                os.remove(video_path)

            return render(request, 'analyze_workout_results.html', {
                'results': analysis_results,
                'success': True
            })

        except Exception as e:
            messages.error(request, f"Error analyzing video: {str(e)}")
            return render(request, 'analyze_workout.html', {'error': str(e)})

    return render(request, 'analyze_workout.html')

@csrf_exempt  # Only for testing, remove in production
def chatbot_view(request):
    if request.method == 'POST':
        try:
            user_message = request.POST.get('message', '')
            if not user_message:
                return JsonResponse({
                    'error': 'No message provided',
                    'response': 'Please send a message to get a response.'
                })

            # Print debug information
            print("API Key:", settings.OPENAI_API_KEY[:5] + "..." if settings.OPENAI_API_KEY else "Not found")
            print("User message:", user_message)

            chatbot = FitnessChatbot()
            response = chatbot.get_response(user_message)
            
            # Print response for debugging
            print("Bot response:", response)
            
            return JsonResponse({
                'response': response,
                'status': 'success'
            })
            
        except Exception as e:
            import traceback
            print("Detailed error:")
            print(traceback.format_exc())
            return JsonResponse({
                'error': str(e),
                'response': f'Error: {str(e)}'
            })
            
    return render(request, 'chatbot.html')

@custom_login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 0))
            
            cart_item = Cart.objects.get(id=item_id, user_id=request.session.get('user_id'))
            product = Product.objects.get(id=cart_item.product_id)

            # Validate quantity
            if quantity <= 0:
                return JsonResponse({
                    'error': 'Quantity must be greater than 0',
                    'current_quantity': cart_item.quantity
                })
            
            if quantity > product.stock:
                return JsonResponse({
                    'error': f'Only {product.stock} items available in stock',
                    'current_quantity': cart_item.quantity
                })

            # Update quantity
            cart_item.quantity = quantity
            cart_item.save()

            return JsonResponse({
                'success': True,
                'message': 'Cart updated successfully',
                'new_quantity': quantity,
                'new_total': str(cart_item.total_price)
            })

        except Cart.DoesNotExist:
            return JsonResponse({
                'error': 'Cart item not found'
            }, status=404)
        except Product.DoesNotExist:
            return JsonResponse({
                'error': 'Product not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'error': 'Invalid request method'
    }, status=405)



@register.filter
def filter_status(orders, status):
    return [order for order in orders if order.status == status]

@custom_login_required
def workout_correction_view(request):
    return render(request, 'workout_correction.html')


def delivery_boy_register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address_line1 = request.POST.get('address_line1')
        city = request.POST.get('city')
        section = request.POST.get('section')  # Added this line
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        vehicle_type = request.POST.get('vehicle_type')
        identity_type = request.POST.get('identity_type')
        
        identity_proof = request.FILES.get('identity_proof')
        vehicle_registration = request.FILES.get('vehicle_registration')
        
        # Handle file storage
        fs = FileSystemStorage()
        identity_proof_name = fs.save(f'delivery_boy/id_proofs/{identity_proof.name}', identity_proof)
        vehicle_doc_name = fs.save(f'delivery_boy/vehicle_docs/{vehicle_registration.name}', vehicle_registration)

        with connection.cursor() as cursor:
            # Check if email already exists
            cursor.execute("SELECT COUNT(*) FROM tbl_delivery_boy WHERE email = %s", [email])
            if cursor.fetchone()[0] > 0:
                messages.error(request, 'Email already registered')
                return render(request, 'delivery_boy_register.html')

            # Check if phone already exists
            cursor.execute("SELECT COUNT(*) FROM tbl_delivery_boy WHERE phone = %s", [phone])
            if cursor.fetchone()[0] > 0:
                messages.error(request, 'Phone number already registered')
                return render(request, 'delivery_boy_register.html')

            # Insert new delivery boy
            cursor.execute("""
                INSERT INTO tbl_delivery_boy 
                (name, email, phone, address_line1, city, section, state, zip_code, 
                vehicle_type, identity_type, identity_proof, vehicle_registration, 
                status, date_joined)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, NOW())
            """, [name, email, phone, address_line1, city, section, state, zip_code,
                  vehicle_type, identity_type, identity_proof_name, vehicle_doc_name])

        messages.success(request, 'Registration successful! Please wait for admin approval.')
        return redirect('delivery_manager_login')

    # Pass the sections list to the template
    sections = ['Kozhikode', 'Thrissur', 'Ernakulam', 'Alappuzha', 'Thiruvananthapuram']
    return render(request, 'delivery_boy_register.html', {'sections': sections})

def delivery_manager_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username,password)
        with connection.cursor() as cursor:
            # Print debug information
            print(f"Attempting login with username: {username}")
            
            # First, check if the credentials exist
            cursor.execute("""
                SELECT user_id, name, status 
                FROM tbl_delivery_boy 
                WHERE username = %s AND password = %s
            """, [username, password])
            result = cursor.fetchone()
            
            if result:
                user_id, name, status = result
                
                if status == 1:  # Approved
                    print("hello")
                    request.session['delivery_boy_id'] = user_id
                    request.session['delivery_boy_name'] = name
                    # return render(request, 'delivery_dashboard.html')
                    # messages.success(request, f'Welcome back, {name}!')
                    # Fix: Use redirect with URL name, not template
                    return redirect('delivery_dashboard')  # Changed this line
                elif status == 0:
                    messages.error(request, 'Your account is still pending approval.')
                elif status == 2:
                    messages.error(request, 'Your application has been rejected.')
                else:
                    messages.error(request, 'Invalid account status.')
            else:
                messages.error(request, 'Invalid username or password.')
                
            # Print debug information if login failed
            cursor.execute("""
                SELECT username, status 
                FROM tbl_delivery_boy 
                WHERE username = %s
            """, [username])
            user_check = cursor.fetchone()
            if user_check:
                print(f"User found with status: {user_check[1]}")
            else:
                print("No user found with this username")
    
    return render(request, 'delivery_manager_login.html')

@delivery_manager_required  # You'll need to create this decorator
def delivery_dashboard(request):
    delivery_boy_id = request.session.get('delivery_boy_id')
    
    with connection.cursor() as cursor:
        # Get delivery boy's section (center)
        cursor.execute("""
            SELECT section 
            FROM tbl_delivery_boy 
            WHERE user_id = %s
        """, [delivery_boy_id])
        delivery_center = cursor.fetchone()[0]
        
        # Get orders for this center that are out for delivery
        cursor.execute("""
            SELECT o.id, o.order_date, o.status, p.name as product_name, 
                   o.quantity, a.address_line1, a.city, a.zip_code,
                   a.contact_number
            FROM app_order o
            JOIN app_product p ON o.product_id = p.id
            JOIN app_address a ON o.address_id = a.id
            WHERE o.delivery_center = %s
            ORDER BY o.order_date DESC
        """, [delivery_center])
        orders = dictfetchall(cursor)
    
    # Count orders by status
    shipped_orders = [order for order in orders if order['status'] == 'Shipped']
    out_for_delivery = [order for order in orders if order['status'] == 'Out for Delivery']
    delivered_orders = [order for order in orders if order['status'] == 'Delivered']
    
    context = {
        'delivery_boy': {'name': request.session.get('delivery_boy_name')},
        'orders': orders,
        'center': delivery_center,
        'shipped_count': len(shipped_orders),
        'out_for_delivery_count': len(out_for_delivery),
        'delivered_count': len(delivered_orders)
    }
    return render(request, 'delivery_dashboard.html', context)

@delivery_manager_required
def delivery_manager_logout(request):
    request.session.flush()
    return redirect('delivery_manager_login')

@admin_custom_login_required
def admin_delivery_boys_view(request):
    with connection.cursor() as cursor:
        # Fetch pending delivery boys
        cursor.execute("""
            SELECT user_id, name, email, phone, city, section, vehicle_type, identity_type, 
                   identity_proof, vehicle_registration, status
            FROM tbl_delivery_boy 
            WHERE status = 0
        """)
        pending_delivery_boys = dictfetchall(cursor)

        # Fetch approved delivery boys
        cursor.execute("""
            SELECT user_id, name, email, phone, city, section, vehicle_type, username, status
            FROM tbl_delivery_boy 
            WHERE status = 1
        """)
        approved_delivery_boys = dictfetchall(cursor)

        # Fetch rejected delivery boys
        cursor.execute("""
            SELECT user_id, name, email, phone, city, section, vehicle_type, status
            FROM tbl_delivery_boy 
            WHERE status = 2
        """)
        rejected_delivery_boys = dictfetchall(cursor)

    context = {
        'pending_delivery_boys': pending_delivery_boys,
        'approved_delivery_boys': approved_delivery_boys,
        'rejected_delivery_boys': rejected_delivery_boys
    }
    return render(request, 'admin_delivery_boys.html', context)
@admin_custom_login_required
def accept_delivery_boy(request, user_id):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            username = get_random_string(8)
            password = get_random_string(12)
            
            cursor.execute("SELECT email FROM tbl_delivery_boy WHERE user_id = %s", [user_id])
            email = cursor.fetchone()[0]
            
            cursor.execute("""
                UPDATE tbl_delivery_boy 
                SET status = 1, username = %s, password = %s 
                WHERE user_id = %s
            """, [username, password, user_id])
            
            # Send email with credentials
            send_mail(
                'Your Delivery Partner Account Has Been Approved - FitSculpt',
                f'Congratulations! Your account has been approved.\n\n'
                f'Username: {username}\n'
                f'Password: {password}\n\n'
                f'You can now login to your delivery dashboard.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'Delivery boy approved and credentials sent')
    
    return redirect('admin_delivery_boys')
@admin_custom_login_required
def reject_delivery_boy(request, user_id):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM tbl_delivery_boy WHERE user_id = %s", [user_id])
            email = cursor.fetchone()[0]
            
            cursor.execute("""
                UPDATE tbl_delivery_boy 
                SET status = 2 
                WHERE user_id = %s
            """, [user_id])
            
            # Send rejection email
            send_mail(
                'FitSculpt Delivery Partner Application Status',
                'We regret to inform you that your application has been rejected. '
                'Thank you for your interest in joining FitSculpt.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'Delivery boy application rejected')
    
    return redirect('admin_delivery_boys')

@delivery_manager_required
def update_order_status(request, order_id):
    try:
        delivery_lat = float(request.POST.get('latitude', 0))
        delivery_lng = float(request.POST.get('longitude', 0))
        delivery_pincode = request.POST.get('pincode')
        entered_otp = request.POST.get('otp')

        print(f"Delivery Boy Location Details:")
        print(f"Latitude: {delivery_lat}")
        print(f"Longitude: {delivery_lng}")
        print(f"Delivery Boy Pincode: {delivery_pincode}")

        if not all([delivery_lat, delivery_lng, delivery_pincode]):
            return JsonResponse({
                'success': False,
                'message': 'Missing required delivery information'
            }, status=400)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT o.id, o.status, o.delivery_otp, o.otp_created_at, 
                       a.zip_code, c.email 
                FROM app_order AS o
                INNER JOIN app_address AS a ON o.address_id = a.id
                INNER JOIN client AS c ON o.user_id = c.user_id
                WHERE o.id = %s
            """, [order_id])
            
            result = dictfetchall(cursor)
            if not result:
                return JsonResponse({
                    'success': False,
                    'message': 'Order not found'
                }, status=404)
                
            result = result[0]
            
            print(f"Delivery Address Details:")
            print(f"Order ID: {result['id']}")
            print(f"Client Pincode: {result['zip_code']}")
            print(f"Comparing Pincodes: {delivery_pincode} == {result['zip_code']}")
            
            # Strict pincode comparison
            if str(delivery_pincode).strip() != str(result['zip_code']).strip():
                print(f"Pincode mismatch! Delivery Boy: {delivery_pincode}, Client: {result['zip_code']}")
                return JsonResponse({
                    'success': False,
                    'message': f'You are currently in pincode {delivery_pincode}. Please go to delivery address pincode {result["zip_code"]} to proceed with delivery.'
                }, status=400)

            print("Pincode verification passed!")

            # Handle OTP verification or generation
            if entered_otp:
                print(f"Verifying OTP: {entered_otp} against {result['delivery_otp']}")
                
                if not result['delivery_otp']:
                    return JsonResponse({
                        'success': False,
                        'message': 'No OTP has been generated. Please request a new OTP.'
                    }, status=400)
                    
                if result['otp_created_at'] and \
                   datetime.now() - result['otp_created_at'] > timedelta(minutes=5):
                    return JsonResponse({
                        'success': False,
                        'message': 'OTP has expired. Please request a new OTP.'
                    }, status=400)
                    
                if entered_otp != result['delivery_otp']:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid OTP'
                    }, status=400)
                
                try:
                    # OTP is valid, update order status
                    cursor.execute("""
                        UPDATE app_order 
                        SET status = 'Delivered',
                            delivered_at = NOW(),
                            delivery_latitude = %s,
                            delivery_longitude = %s
                        WHERE id = %s
                    """, [delivery_lat, delivery_lng, order_id])
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Order marked as delivered successfully'
                    })
                except Exception as e:
                    print(f"Error updating order status: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Error updating order status in database'
                    }, status=500)
            else:
                # Generate new OTP
                new_otp = ''.join(random.choices('0123456789', k=6))
                otp_created_at = datetime.now()
                
                print(f"Generating new OTP: {new_otp}")
                
                try:
                    # Update order with new OTP
                    cursor.execute("""
                        UPDATE app_order 
                        SET delivery_otp = %s,
                            otp_created_at = %s
                        WHERE id = %s
                    """, [new_otp, otp_created_at, order_id])
                    
                    # Send OTP to user's email
                    send_mail(
                        'Delivery OTP for Your FitSculpt Order',
                        f'Your delivery OTP is: {new_otp}\nValid for 5 minutes.',
                        settings.DEFAULT_FROM_EMAIL,
                        [result['email']],
                        fail_silently=False,
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'OTP has been sent to customer email',
                        'requireOTP': True
                    })
                except Exception as e:
                    print(f"Error generating/sending OTP: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Error generating or sending OTP'
                    }, status=500)
            
    except Exception as e:
        print(f"Error in update_order_status: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }, status=500)

@delivery_manager_required
def clear_delivery_message(request):
    if request.method == 'POST':
        if 'delivery_success' in request.session:
            del request.session['delivery_success']
        if 'delivery_error' in request.session:
            del request.session['delivery_error']
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)

@custom_login_required
def community_view(request):
    user_id = request.session.get('user_id')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        
        try:
            if image:
                # Validate image content
                image_validator = ImageValidator()
                is_valid, label, confidence = image_validator.is_fitness_related(image.read())
                
                if not is_valid:
                    messages.error(request, 
                        f"Please upload only fitness, workout, or nutrition related images. "
                        f"Detected: {label} (Confidence: {confidence:.2f}). "
                        "Try an image showing exercise, healthy food, or fitness activities.")
                    return redirect('community')
                
                # Reset file pointer after reading
                image.seek(0)
                
                # Generate unique filename
                ext = image.name.split('.')[-1]
                filename = f"community_posts/{user_id}_{int(time.time())}.{ext}"
                
                # Save image
                fs = FileSystemStorage()
                filename = fs.save(filename, image)
            else:
                filename = None
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tbl_community_posts (user_id, content, image, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, [user_id, content, filename])
            
            messages.success(request, 'Post created successfully!')
            
        except Exception as e:
            messages.error(request, f'Error creating post: {str(e)}')
        
        return redirect('community')
    
    # Handle GET request
    with connection.cursor() as cursor:
        # Get all posts with user details
        cursor.execute("""
            SELECT 
                cp.id,
                cp.user_id,
                cp.content,
                cp.image,
                cp.created_at,
                cp.likes,
                c.name,
                c.profile_picture 
            FROM tbl_community_posts cp
            JOIN client c ON cp.user_id = c.user_id
            ORDER BY cp.created_at DESC
        """)
        posts = dictfetchall(cursor)
        
        # Process image URLs
        for post in posts:
            if post['image']:
                post['image_url'] = f"{settings.MEDIA_URL}{post['image']}"
            if post['profile_picture']:
                post['profile_picture_url'] = f"{settings.MEDIA_URL}{post['profile_picture']}"
        
        # Get comments for each post
        for post in posts:
            cursor.execute("""
                SELECT pc.*, c.name, c.profile_picture 
                FROM tbl_post_comments pc
                JOIN client c ON pc.user_id = c.user_id
                WHERE pc.post_id = %s
                ORDER BY pc.created_at DESC
            """, [post['id']])
            comments = dictfetchall(cursor)
            
            # Process profile pictures for comments
            for comment in comments:
                if comment['profile_picture']:
                    comment['profile_picture_url'] = f"{settings.MEDIA_URL}{comment['profile_picture']}"
            
            post['comments'] = comments
            
            # Check if current user has liked the post
            cursor.execute("""
                SELECT COUNT(*) as liked
                FROM tbl_post_likes
                WHERE post_id = %s AND user_id = %s
            """, [post['id'], user_id])
            post['user_has_liked'] = dictfetchall(cursor)[0]['liked'] > 0
    
    return render(request, 'community.html', {'posts': posts})

@custom_login_required
def like_post(request, post_id):
    user_id = request.session.get('user_id')
    
    try:
        with connection.cursor() as cursor:
            # Check if user has already liked the post
            cursor.execute("""
                SELECT COUNT(*) as liked
                FROM tbl_post_likes
                WHERE post_id = %s AND user_id = %s
            """, [post_id, user_id])
            
            already_liked = dictfetchall(cursor)[0]['liked'] > 0
            
            if already_liked:
                # Unlike the post
                cursor.execute("""
                    DELETE FROM tbl_post_likes
                    WHERE post_id = %s AND user_id = %s
                """, [post_id, user_id])
                
                # Update post likes count
                cursor.execute("""
                    UPDATE tbl_community_posts
                    SET likes = likes - 1
                    WHERE id = %s
                """, [post_id])
                
                return JsonResponse({'status': 'unliked', 'likes': get_post_likes(post_id)})
            else:
                # Like the post
                cursor.execute("""
                    INSERT INTO tbl_post_likes (post_id, user_id, created_at)
                    VALUES (%s, %s, NOW())
                """, [post_id, user_id])
                
                # Update post likes count
                cursor.execute("""
                    UPDATE tbl_community_posts
                    SET likes = likes + 1
                    WHERE id = %s
                """, [post_id])
                
                return JsonResponse({'status': 'liked', 'likes': get_post_likes(post_id)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@custom_login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        comment = request.POST.get('comment')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tbl_post_comments (post_id, user_id, comment, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, [post_id, user_id, comment])
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_post_likes(post_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT likes FROM tbl_community_posts WHERE id = %s
        """, [post_id])
        return dictfetchall(cursor)[0]['likes']

@custom_login_required
def community_profile(request):
    user_id = request.session.get('user_id')
    viewing_user_id = user_id  # Add this line - in profile view, viewer is the same as profile owner
    
    with connection.cursor() as cursor:
        # Get user profile
        cursor.execute("""
            SELECT name, profile_picture
            FROM client
            WHERE user_id = %s
        """, [user_id])
        user_profile = dictfetchall(cursor)[0]
        
        if user_profile['profile_picture']:
            user_profile['profile_picture_url'] = f"{settings.MEDIA_URL}{user_profile['profile_picture']}"
        
        # Get followers and following counts
        followers_count, following_count = get_follow_counts(cursor, user_id)
        
        # Get followers list with their follow status
        cursor.execute("""
            SELECT c.user_id, c.name, c.profile_picture,
                   EXISTS(SELECT 1 FROM tbl_followers 
                         WHERE follower_id = %s AND following_id = c.user_id) as is_following
            FROM tbl_followers f
            JOIN client c ON f.follower_id = c.user_id
            WHERE f.following_id = %s
        """, [viewing_user_id, user_id])
        followers = dictfetchall(cursor)
        
        # Get following list
        cursor.execute("""
            SELECT c.user_id, c.name, c.profile_picture,
                   EXISTS(SELECT 1 FROM tbl_followers 
                         WHERE follower_id = %s AND following_id = c.user_id) as is_following
            FROM tbl_followers f
            JOIN client c ON f.following_id = c.user_id
            WHERE f.follower_id = %s
        """, [viewing_user_id, user_id])
        following = dictfetchall(cursor)
        
        # Process profile pictures
        for user in followers + following:
            if user['profile_picture']:
                user['profile_picture_url'] = f"{settings.MEDIA_URL}{user['profile_picture']}"
        
        # Get user's posts with likes count and comments count
        cursor.execute("""
            SELECT cp.*, 
                   (SELECT COUNT(*) FROM tbl_post_likes WHERE post_id = cp.id) as likes_count,
                   (SELECT COUNT(*) FROM tbl_post_comments WHERE post_id = cp.id) as comments_count,
                   EXISTS(SELECT 1 FROM tbl_post_likes WHERE post_id = cp.id AND user_id = %s) as user_has_liked
            FROM tbl_community_posts cp
            WHERE cp.user_id = %s
            ORDER BY cp.created_at DESC
        """, [viewing_user_id, user_id])
        posts = dictfetchall(cursor)
        
        # Process posts
        for post in posts:
            if post['image']:
                post['image_url'] = f"{settings.MEDIA_URL}{post['image']}"
            
            cursor.execute("""
                SELECT pc.*, c.name, c.profile_picture
                FROM tbl_post_comments pc
                JOIN client c ON pc.user_id = c.user_id
                WHERE pc.post_id = %s
                ORDER BY pc.created_at DESC
            """, [post['id']])
            post['comments'] = dictfetchall(cursor)
    
    context = {
        'user_profile': user_profile,
        'followers_count': followers_count,
        'following_count': following_count,
        'followers': followers,
        'following': following,
        'user_posts': posts,
        'posts_count': len(posts),
        'profile_view': True
    }
    
    return render(request, 'community_profile.html', context)

@custom_login_required
def community_search(request):
    query = request.GET.get('q', '')
    viewing_user_id = request.session.get('user_id')
    
    with connection.cursor() as cursor:
        if query:
            cursor.execute("""
                SELECT c.user_id, c.name, c.profile_picture,
                       (SELECT COUNT(*) FROM tbl_community_posts WHERE user_id = c.user_id) as posts_count,
                       EXISTS(SELECT 1 FROM tbl_followers 
                            WHERE follower_id = %s AND following_id = c.user_id) as is_following
                FROM client c
                WHERE c.name LIKE %s AND c.status = 1 AND c.user_id != %s
                ORDER BY c.name
            """, [viewing_user_id, f'%{query}%', viewing_user_id])
        else:
            cursor.execute("""
                SELECT c.user_id, c.name, c.profile_picture,
                       (SELECT COUNT(*) FROM tbl_community_posts WHERE user_id = c.user_id) as posts_count,
                       EXISTS(SELECT 1 FROM tbl_followers 
                            WHERE follower_id = %s AND following_id = c.user_id) as is_following
                FROM client c
                WHERE c.status = 1 AND c.user_id != %s
                ORDER BY c.name
            """, [viewing_user_id, viewing_user_id])
        
        users = dictfetchall(cursor)
        
        for user in users:
            if user['profile_picture']:
                user['profile_picture_url'] = f"{settings.MEDIA_URL}{user['profile_picture']}"
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'search_results.html', {'users': users})
    
    return render(request, 'community_search.html', {
        'users': users,
        'query': query
    })

@custom_login_required
def community_messenger(request):
    user_id = request.session.get('user_id')
    chat_with = request.GET.get('user')
    
    with connection.cursor() as cursor:
        # Get all chats ordered by most recent message
        cursor.execute("""
            SELECT DISTINCT 
                c.user_id, c.name, c.profile_picture,
                (SELECT content 
                 FROM tbl_community_messages 
                 WHERE (sender_id = c.user_id AND recipient_id = %s)
                    OR (sender_id = %s AND recipient_id = c.user_id)
                 ORDER BY created_at DESC
                 LIMIT 1) as last_message,
                (SELECT created_at
                 FROM tbl_community_messages 
                 WHERE (sender_id = c.user_id AND recipient_id = %s)
                    OR (sender_id = %s AND recipient_id = c.user_id)
                 ORDER BY created_at DESC
                 LIMIT 1) as last_message_time
            FROM tbl_community_messages m
            JOIN client c ON (m.sender_id = c.user_id OR m.recipient_id = c.user_id)
            WHERE (m.sender_id = %s OR m.recipient_id = %s)
                AND c.user_id != %s
            GROUP BY c.user_id, c.name, c.profile_picture
            ORDER BY last_message_time DESC  # Added this ORDER BY clause
        """, [user_id, user_id, user_id, user_id, user_id, user_id, user_id])
        
        chats = dictfetchall(cursor)
        
        # Add profile picture URLs
        for chat in chats:
            if chat['profile_picture']:
                chat['profile_picture_url'] = f"{settings.MEDIA_URL}{chat['profile_picture']}"
        
        active_chat = None
        messages = []
        
        if chat_with:
            # Get active chat user details
            cursor.execute("""
                SELECT user_id, name, profile_picture
                FROM client
                WHERE user_id = %s
            """, [chat_with])
            active_chat = dictfetchall(cursor)[0]
            
            # Add profile picture URL for active chat
            if active_chat['profile_picture']:
                active_chat['profile_picture_url'] = f"{settings.MEDIA_URL}{active_chat['profile_picture']}"
            
            # Get messages
            cursor.execute("""
                SELECT *
                FROM tbl_community_messages
                WHERE (sender_id = %s AND recipient_id = %s)
                   OR (sender_id = %s AND recipient_id = %s)
                ORDER BY created_at
            """, [user_id, chat_with, chat_with, user_id])
            messages = dictfetchall(cursor)
    
    return render(request, 'community_messenger.html', {
        'chats': chats,
        'active_chat': active_chat,
        'messages': messages
    })

@custom_login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = request.session.get('user_id')
        recipient_id = data.get('recipient_id')
        message = data.get('message')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tbl_community_messages (sender_id, recipient_id, content, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, [user_id, recipient_id, message])
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@custom_login_required
def view_user_profile(request, user_id):
    viewing_user_id = request.session.get('user_id')
    
    with connection.cursor() as cursor:
        # Get user details
        cursor.execute("""
            SELECT user_id, name, profile_picture
            FROM client
            WHERE user_id = %s AND status = 1
        """, [user_id])
        user_result = dictfetchall(cursor)
        
        if not user_result:
            messages.error(request, "User not found")
            return redirect('community')
            
        viewed_user = user_result[0]
        if viewed_user['profile_picture']:
            viewed_user['profile_picture_url'] = f"{settings.MEDIA_URL}{viewed_user['profile_picture']}"
        
        # Check if the viewing user is following this user
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM tbl_followers 
                WHERE follower_id = %s AND following_id = %s
            ) as is_following
        """, [viewing_user_id, user_id])
        is_following = cursor.fetchone()[0]
        
        # Get followers and following counts
        followers_count, following_count = get_follow_counts(cursor, user_id)
        
        # Get followers list with their follow status
        cursor.execute("""
            SELECT c.user_id, c.name, c.profile_picture,
                   EXISTS(SELECT 1 FROM tbl_followers 
                         WHERE follower_id = %s AND following_id = c.user_id) as is_following
            FROM tbl_followers f
            JOIN client c ON f.follower_id = c.user_id
            WHERE f.following_id = %s
        """, [viewing_user_id, user_id])
        followers = dictfetchall(cursor)
        
        # Get following list
        cursor.execute("""
            SELECT c.user_id, c.name, c.profile_picture,
                   EXISTS(SELECT 1 FROM tbl_followers 
                         WHERE follower_id = %s AND following_id = c.user_id) as is_following
            FROM tbl_followers f
            JOIN client c ON f.following_id = c.user_id
            WHERE f.follower_id = %s
        """, [viewing_user_id, user_id])
        following = dictfetchall(cursor)
        
        # Process profile pictures
        for user in followers + following:
            if user['profile_picture']:
                user['profile_picture_url'] = f"{settings.MEDIA_URL}{user['profile_picture']}"
        
        # Get user's posts with likes count and comments count
        cursor.execute("""
            SELECT cp.*, 
                   (SELECT COUNT(*) FROM tbl_post_likes WHERE post_id = cp.id) as likes_count,
                   (SELECT COUNT(*) FROM tbl_post_comments WHERE post_id = cp.id) as comments_count,
                   EXISTS(SELECT 1 FROM tbl_post_likes WHERE post_id = cp.id AND user_id = %s) as user_has_liked
            FROM tbl_community_posts cp
            WHERE cp.user_id = %s
            ORDER BY cp.created_at DESC
        """, [viewing_user_id, user_id])
        posts = dictfetchall(cursor)
        
        # Process posts
        for post in posts:
            if post['image']:
                post['image_url'] = f"{settings.MEDIA_URL}{post['image']}"
            
            cursor.execute("""
                SELECT pc.*, c.name, c.profile_picture
                FROM tbl_post_comments pc
                JOIN client c ON pc.user_id = c.user_id
                WHERE pc.post_id = %s
                ORDER BY pc.created_at DESC
            """, [post['id']])
            post['comments'] = dictfetchall(cursor)
    
    context = {
        'viewed_user': viewed_user,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'followers': followers,
        'following': following,
        'user_posts': posts,
        'posts_count': len(posts)
    }
    
    return render(request, 'user_profile_view.html', context)

@custom_login_required
def get_post_details(request, post_id):
    user_id = request.session.get('user_id')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cp.*, c.name as username, c.profile_picture,
                   (SELECT COUNT(*) FROM tbl_post_likes WHERE post_id = cp.id) as likes_count,
                   EXISTS(SELECT 1 FROM tbl_post_likes WHERE post_id = cp.id AND user_id = %s) as user_has_liked,
                   cp.user_id = %s as is_owner
            FROM tbl_community_posts cp
            JOIN client c ON cp.user_id = c.user_id
            WHERE cp.id = %s
        """, [user_id, user_id, post_id])
        
        post = dictfetchall(cursor)[0]
        
        # Get likes
        cursor.execute("""
            SELECT c.user_id, c.name as username, c.profile_picture
            FROM tbl_post_likes pl
            JOIN client c ON pl.user_id = c.user_id
            WHERE pl.post_id = %s
            ORDER BY pl.created_at DESC
        """, [post_id])
        likes = dictfetchall(cursor)
        
        # Get comments
        cursor.execute("""
            SELECT pc.*, c.user_id, c.name as username, c.profile_picture
            FROM tbl_post_comments pc
            JOIN client c ON pc.user_id = c.user_id
            WHERE pc.post_id = %s
            ORDER BY pc.created_at DESC
        """, [post_id])
        comments = dictfetchall(cursor)
        
        response_data = {
            'id': post['id'],
            'image_url': f"{settings.MEDIA_URL}{post['image']}" if post['image'] else None,
            'user_image_url': f"{settings.MEDIA_URL}{post['profile_picture']}" if post['profile_picture'] else None,
            'username': post['username'],
            'caption': post['content'],
            'timestamp': post['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
            'likes_count': post['likes_count'],
            'user_has_liked': post['user_has_liked'],
            'likes': [{
                'user_id': like['user_id'],
                'username': like['username'],
                'profile_picture': f"{settings.MEDIA_URL}{like['profile_picture']}" if like['profile_picture'] else None
            } for like in likes],
            'comments': [{
                'user_id': comment['user_id'],
                'username': comment['username'],
                'content': comment['comment'],
                'timestamp': comment['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'user_image': f"{settings.MEDIA_URL}{comment['profile_picture']}" if comment['profile_picture'] else None
            } for comment in comments],
            'is_owner': post['is_owner'],  # Add this field
        }
        
        return JsonResponse(response_data)

@custom_login_required
def delete_post(request, post_id):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        
        with connection.cursor() as cursor:
            # First verify the post belongs to the user
            cursor.execute("""
                SELECT user_id, image FROM tbl_community_posts
                WHERE id = %s
            """, [post_id])
            result = cursor.fetchone()
            
            if not result:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Post not found'
                }, status=404)
                
            if result[0] != user_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You do not have permission to delete this post'
                }, status=403)
            
            try:
                # Delete related records first
                cursor.execute("DELETE FROM tbl_post_likes WHERE post_id = %s", [post_id])
                cursor.execute("DELETE FROM tbl_post_comments WHERE post_id = %s", [post_id])
                
                # Delete the post
                cursor.execute("DELETE FROM tbl_community_posts WHERE id = %s", [post_id])
                
                # If post had an image, delete it from media folder
                if result[1]:  # result[1] contains the image path
                    image_path = os.path.join(settings.MEDIA_ROOT, result[1])
                    if os.path.exists(image_path):
                        os.remove(image_path)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Post deleted successfully'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

@custom_login_required
def toggle_follow(request, user_id):
    if request.method == 'POST':
        follower_id = request.session.get('user_id')
        
        if follower_id == user_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot follow yourself'
            })
        
        with connection.cursor() as cursor:
            # Check if already following
            cursor.execute("""
                SELECT id FROM tbl_followers 
                WHERE follower_id = %s AND following_id = %s
            """, [follower_id, user_id])
            
            if cursor.fetchone():
                # Unfollow
                cursor.execute("""
                    DELETE FROM tbl_followers 
                    WHERE follower_id = %s AND following_id = %s
                """, [follower_id, user_id])
                action = 'unfollowed'
            else:
                # Follow
                cursor.execute("""
                    INSERT INTO tbl_followers (follower_id, following_id)
                    VALUES (%s, %s)
                """, [follower_id, user_id])
                action = 'followed'
            
        return JsonResponse({
            'status': 'success',
            'action': action
        })
    
    return JsonResponse({'status': 'error'})

def get_follow_counts(cursor, user_id):
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM tbl_followers WHERE following_id = %s) as followers_count,
            (SELECT COUNT(*) FROM tbl_followers WHERE follower_id = %s) as following_count
    """, [user_id, user_id])
    return cursor.fetchone()

from django.shortcuts import render, redirect
from .models import WeeklyWorkoutCompletion, WeeklyNutritionCompletion, Workout, Nutrition

@custom_login_required
def mark_workout_completed(request, workout_id):
    user_id = request.session.get('user_id')
    current_datetime = datetime.now()

    with connection.cursor() as cursor:
        # Get the current day for this workout
        cursor.execute("""
            SELECT s.day, s.service_no
            FROM tbl_services s 
            JOIN tbl_workouts w ON s.workout_id = w.workout_id 
            WHERE w.workout_id = %s
        """, [workout_id])
        current_day, service_no = cursor.fetchone()

        # If this is day 1, use current date as week_start_date
        if current_day == 1:
            week_start_date = current_datetime.date()
        else:
            # Get the week_start_date from day 1's completion
            cursor.execute("""
                SELECT MIN(wc.completion_date)
                FROM WeeklyWorkoutCompletion wc
                JOIN tbl_services s ON wc.workout_id = s.workout_id
                WHERE wc.client_id = %s 
                AND s.day = 1
                AND s.service_no = %s
                AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
            """, [user_id, service_no])
            
            day1_completion = cursor.fetchone()[0]
            if not day1_completion:
                messages.error(request, "Please complete Day 1 workouts first")
                return redirect('workouts_by_day', day=1)
            week_start_date = day1_completion.date()

        # Rest of your existing code...
        cursor.execute("""
            INSERT INTO WeeklyWorkoutCompletion 
            (client_id, week_start_date, workout_completed, workout_id, completion_date)
            VALUES (%s, %s, TRUE, %s, NOW())
        """, [user_id, week_start_date, workout_id])

        messages.success(request, "Workout marked as completed!")
        return redirect('workouts_by_day', day=current_day)

@custom_login_required
def mark_nutrition_completed(request, day):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        current_datetime = datetime.now()
        status = request.POST.get('status', 'completed')

        with connection.cursor() as cursor:
            # First check if ANY nutrition for this day is already completed
            cursor.execute("""
                SELECT COUNT(*) 
                FROM WeeklyNutritionCompletion wc
                JOIN tbl_nutritions n ON wc.nutrition_id = n.nutrition_id
                WHERE wc.client_id = %s 
                AND n.nutrition_no = %s
                AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
            """, [user_id, day])
            
            completion_count = cursor.fetchone()[0]
            if completion_count > 0:
                messages.error(request, f"Day {day} has already been marked as completed")
                return redirect('nutrition')

            # Get the week_start_date from Day 1's completion if it exists
            cursor.execute("""
                SELECT week_start_date
                FROM WeeklyNutritionCompletion wc
                JOIN tbl_nutritions n ON wc.nutrition_id = n.nutrition_id
                WHERE wc.client_id = %s 
                AND n.nutrition_no = 1
                AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
                LIMIT 1
            """, [user_id])
            
            week_start_result = cursor.fetchone()
            week_start_date = week_start_result[0] if week_start_result else current_datetime.date()

            # For days after day 1, check if previous day is completed
            if day > 1:
                cursor.execute("""
                    SELECT completion_date
                    FROM WeeklyNutritionCompletion wc
                    JOIN tbl_nutritions n ON wc.nutrition_id = n.nutrition_id
                    WHERE wc.client_id = %s 
                    AND n.nutrition_no = %s
                    AND wc.completion_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
                    ORDER BY wc.completion_date DESC
                    LIMIT 1
                """, [user_id, day - 1])
                
                result = cursor.fetchone()
                if not result:
                    messages.error(request, f"Please complete Day {day-1} first")
                    return redirect('nutrition')
                
                prev_day_completion = result[0]
                hours_passed = (current_datetime - prev_day_completion).total_seconds() / 3600
                
                if hours_passed < 24:
                    messages.error(request, f"Please wait {int(24 - hours_passed)} more hours before completing Day {day}")
                    return redirect('nutrition')

            try:
                # Start a transaction
                cursor.execute("START TRANSACTION")
                
                # Get nutrition IDs for the current day
                cursor.execute("""
                    SELECT nutrition_id 
                    FROM tbl_nutritions 
                    WHERE nutrition_no = %s
                """, [day])
                
                nutrition_ids = [row[0] for row in cursor.fetchall()]
                
                # Insert completion records using the consistent week_start_date
                completion_time = current_datetime
                for nutrition_id in nutrition_ids:
                    cursor.execute("""
                        INSERT INTO WeeklyNutritionCompletion 
                        (client_id, week_start_date, nutrition_completed, nutrition_id, completion_date)
                        VALUES (%s, %s, %s, %s, %s)
                    """, [user_id, week_start_date, status == 'completed', nutrition_id, completion_time])

                # Commit the transaction
                cursor.execute("COMMIT")
                
                messages.success(request, f"Day {day}'s nutrition plan marked as {'followed' if status == 'completed' else 'not followed'}")
                
                # Modified redirect logic
                next_day = day + 1
                if next_day <= 7:
                    # Use the proper URL format
                    return redirect('nutrition')  # This will redirect to base nutrition URL
                else:
                    return redirect('nutrition')
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('nutrition')

    return redirect('nutrition')

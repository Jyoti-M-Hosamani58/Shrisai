import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, reverse, redirect, get_object_or_404

from consign_app.models import Login, AddConsignment,ConsignmentHistory,AddConsignmentTemp,Stages,Parties, AddTrack,FeedBack,Category, Branch,Driver,Vehicle, Staff,Consignee, Consignor,TripSheetTemp,TripSheetPrem, Account,Expenses
#from django.core.mail import send_mail

import datetime
import random
import string
import secrets

from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
from consign.settings import BASE_DIR
from django.db.models import Q, Max, Min, Subquery, OuterRef
from django.contrib import messages
from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse, Http404
import json
from django.views.decorators.http import require_POST
from django.db.models import Count
from datetime import datetime
from django.core.exceptions import ValidationError
from decimal import Decimal

from django.db.models.functions import Concat
from django.db import connection, IntegrityError, transaction

from .models import Location  # Assume you have a Location model

#import datetime
#from .models import AddTrack, AddConsignment
from barcode.writer import ImageWriter
from django.conf import settings
import barcode
from django.core.files import File
from barcode import Code128  # Use Code128 or any other suitable barcode format
from django.core.exceptions import FieldError
import traceback  # To get detailed error trace if needed

from django.views.decorators.http import require_GET


# Create your views here.
def index(request):
    return render(request,'index.html')



def feedback(request):
    uid = request.session.get('username')
    if not uid:
        return redirect('login')  # Redirect to login if session does not have username

    # Fetch only the receiver_email column
    userdata = AddConsignment.objects.filter(receiver_email=uid).values_list('receiver_email', flat=True)

    if request.method == "POST":
        feed = request.POST.get('feedback')

        if userdata.exists():
            username = userdata[0]  # Extract the first email from the list

            FeedBack.objects.create(
                username=username,
                feedback=feed
            )
            messages.success(request, 'Feedback sent successfully')
            return redirect('feedback')
        else:
            messages.error(request, 'User not found')
            return render(request, 'feedback.html')

    return render(request, 'feedback.html')

def view_feedback(request):
    userdata=FeedBack.objects.all()
    return render(request,'view_feedback.html',{'userdata':userdata})



def staff_nav(request):
    return render(request,'staff_nav.html')



def index_menu(request):
    return render(request,'index_menu.html')

def admin_home(request):
    return render(request,'admin_home.html')

def user_home(request):
    return render(request,'user_home.html')

def user_home(request):
    return render(request,'user_home.html')

def user_menu(request):
    return render(request,'user_menu.html')

def nav(request):
    return render(request,'nav.html')




def userlogin(request):
    if request.method=="POST":
        username=request.POST.get('t1')
        password=request.POST.get('t2')
        request.session['username']=username
        ucount=Login.objects.filter(username=username).count()
        if ucount>=1:
            udata = Login.objects.get(username=username)
            upass = udata.password
            utype=udata.utype
            if password == upass:
                request.session['utype'] = utype
                if utype == 'user':
                    return redirect('user_home.html')
                if utype == 'admin':
                    return render(request,'admin_home.html')
                if utype == 'branch':
                    return redirect('branch_home')  # Redirect to branch home if login is successful
                if utype == 'staff':
                    return redirect('staff_home')
                if utype == 'customer':
                    return redirect('customerConsignment')
            else:
                return render(request,'userlogin.html',{'msg':'Invalid Password'})
        else:
            return render(request,'userlogin.html',{'msg':'Invalid Username'})
    return render(request,'userlogin.html')


def logout(request):
    return render(request,'index.html')

def branch_home(request):
    uid = request.session.get('username')
    branch = None
    if uid:
        try:
            branch = Branch.objects.get(email=uid)
        except Branch.DoesNotExist:
            branch = None

    return render(request, 'branch_home.html', {'branch': branch})

def staff_home(request):
    uid = request.session.get('username')
    branch = None
    if uid:
        try:
            staff = Staff.objects.get(staffPhone=uid)
            company = staff.Branch
            branch = Branch.objects.get(companyname=company)
        except Branch.DoesNotExist:
            branch = None
    return render(request,'staff_home.html',{'branch':branch})

from django.core.exceptions import ValidationError
from django.db import IntegrityError
import logging

# Set up a logger for this module
logger = logging.getLogger(__name__)

def addConsignment(request):
    if request.method == "POST":
        try:
            now = datetime.now()
            con_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")

            uid = request.session.get('username')
            branch = Staff.objects.get(staffPhone=uid)
            uname = branch.Branch
            username = branch.staffname

            # Get the last track_id and increment it
            last_track_id = AddConsignment.objects.aggregate(Max('track_id'))['track_id__max']
            track_id = int(last_track_id) + 1 if last_track_id else 1001
            con_id = str(track_id)

            # Get the last Consignment_id and increment it
            last_con_id = AddConsignment.objects.aggregate(Max('Consignment_id'))['Consignment_id__max']
            Consignment_id = last_con_id + 1 if last_con_id else 1001
            Consignment_id = str(Consignment_id)

            # Sender and Receiver details
            send_name = request.POST.get('a1')
            send_mobile = request.POST.get('a2')
            send_address = request.POST.get('a4')
            sender_GST = request.POST.get('sendergst')
            rec_name = request.POST.get('a5')
            rec_mobile = request.POST.get('a6')
            rec_address = request.POST.get('a8')
            rec_GST = request.POST.get('receivergst')
            route_from = request.POST.get('from')
            route_to = request.POST.get('to')

            # Validation for required fields
            if not send_name or not rec_name:
                error_message = 'Sender and Receiver names are required.'
                logger.error(error_message)  # Log error details
                return JsonResponse({'error': error_message}, status=400)

            # Check if route_to matches any location in Location model
            location_match = Location.objects.filter(location=route_to).exists()
            if not location_match:
                invalid_locations = Location.objects.values_list('location', flat=True)
                error_message = f'The destination route does not match the allowed locations: {", ".join(invalid_locations)}.'
                logger.warning(error_message)  # Log warning for invalid locations
                return JsonResponse({'error': error_message}, status=400)

            # Check if route_to matches any location in Location model
            location_from = Location.objects.filter(location=route_from).exists()
            if not location_from:
                invalid_locations = Location.objects.values_list('location', flat=True)
                error_message = f'The From route does not match the allowed locations: {", ".join(invalid_locations)}.'
                logger.warning(error_message)  # Log warning for invalid locations
                return JsonResponse({'error': error_message}, status=400)

            # Copies (consignor, consignee, etc.)
            copies = []
            if request.POST.get('consignor_copy'):
                copies.append('Consignor Copy')
            if request.POST.get('consignee_copy'):
                copies.append('Consignee Copy')
            if request.POST.get('lorry_copy'):
                copies.append('Lorry Copy')
            copy_type = ', '.join(copies)

            # Create or update Consignor
            try:
                consignor, _ = Consignor.objects.update_or_create(
                    sender_name=send_name,
                    defaults={
                        'sender_mobile': send_mobile,
                        'sender_address': send_address,
                        'sender_GST': sender_GST,
                        'branch': uname,
                        'username': username
                    }
                )
            except (IntegrityError, ValidationError) as e:
                logger.exception("Error saving consignor")  # Log the complete traceback
                return JsonResponse({'error': 'Error saving consignor. Please check your inputs.'}, status=400)

            # Create or update Consignee
            try:
                consignee, _ = Consignee.objects.update_or_create(
                    receiver_name=rec_name,
                    defaults={
                        'receiver_mobile': rec_mobile,
                        'receiver_address': rec_address,
                        'receiver_GST': rec_GST,
                        'branch': uname,
                        'username': username
                    }
                )
            except (IntegrityError, ValidationError) as e:
                logger.exception("Error saving consignee")  # Log the complete traceback
                return JsonResponse({'error': 'Error saving consignee. Please check your inputs.'}, status=400)

            # Other consignment details
            remark = request.POST.get('remark')
            delivery = request.POST.get('delivery_option')
            pieces = request.POST.get('packages')
            prod_price = request.POST.get('prod_price')
            eway_bill = request.POST.get('ewaybill_no')
            weight = request.POST.get('weight')
            category = request.POST.get('category')
            freight = float(request.POST.get('freight', 0))
            hamali = request.POST.get('hamali', 0)
            door_charge = request.POST.get('door_charge', 0)
            cgst = request.POST.get('cgst', 0)
            sgst = request.POST.get('sgst', 0)
            gst = request.POST.get('gst', 0)
            cost = float(request.POST.get('cost', 0))
            pay_status = request.POST.get('payment')

            unique_id = str(uuid.uuid4().int)[:12]
            utype = request.session.get('utype')
            branch_value = 'admin' if utype == 'admin' else uname

            # Determine the appropriate name based on pay_status
            account_name = send_name if pay_status == 'Shipper A/C' else rec_name if pay_status == 'Receiver A/C' else send_name

            # Save to AddConsignment
            try:
                consignment = AddConsignment.objects.create(
                    track_id=con_id,
                    Consignment_id=Consignment_id,
                    sender_name=send_name,
                    sender_mobile=send_mobile,
                    sender_address=send_address,
                    sender_GST=sender_GST,
                    receiver_name=rec_name,
                    receiver_mobile=rec_mobile,
                    receiver_address=rec_address,
                    receiver_GST=rec_GST,
                    pieces=pieces,
                    prod_price=prod_price,
                    category=category,
                    weight=weight,
                    freight=freight,
                    hamali=hamali,
                    door_charge=door_charge,
                    gst=gst,
                    cgst=cgst,
                    sgst=sgst,
                    route_from=route_from,
                    route_to=route_to,
                    total_cost=cost,
                    date=con_date,
                    pay_status=pay_status,
                    branch=branch_value,
                    name=username,
                    time=current_time,
                    copy_type=copy_type,
                    delivery=delivery,
                    eway_bill=eway_bill,
                    barcode_number=unique_id,
                    remark=remark,
                    status='Active',
                    reason='Consignment Added'
                )
                consignmenttemp = AddConsignmentTemp.objects.create(
                    track_id=con_id,
                    Consignment_id=Consignment_id,
                    sender_name=send_name,
                    sender_mobile=send_mobile,
                    sender_address=send_address,
                    sender_GST=sender_GST,
                    receiver_name=rec_name,
                    receiver_mobile=rec_mobile,
                    receiver_address=rec_address,
                    receiver_GST=rec_GST,
                    pieces=pieces,
                    prod_price=prod_price,
                    category=category,
                    weight=weight,
                    freight=freight,
                    hamali=hamali,
                    door_charge=door_charge,
                    gst=gst,
                    cgst=cgst,
                    sgst=sgst,
                    route_from=route_from,
                    route_to=route_to,
                    total_cost=cost,
                    date=con_date,
                    pay_status=pay_status,
                    branch=branch_value,
                    name=username,
                    time=current_time,
                    copy_type=copy_type,
                    delivery=delivery,
                    eway_bill=eway_bill,
                    barcode_number=unique_id,
                    remark=remark,
                    status='Active',
                    reason='Consignment Added'
                )
                ConsignmentHistory.objects.create(
                    track_id=con_id,
                    sender_name=send_name,
                    sender_mobile=send_mobile,
                    sender_address=send_address,
                    receiver_name=rec_name,
                    receiver_mobile=rec_mobile,
                    receiver_address=rec_address,
                    total_cost=cost,
                    date=con_date,
                    pay_status=pay_status,
                    route_from=route_from,
                    route_to=route_to,
                    pieces=pieces,
                    name=username,
                    time=current_time,
                    eway_bill=eway_bill,
                    category=category,
                    comment='Consignment Added'
                )

                # Convert track_id to a string
                track_id_str = str(track_id)

                # Check the length of track_id
                if len(track_id_str) < 12:
                    barcode_number = track_id_str.zfill(12)  # Ensure 12 digits for EAN-13
                elif len(track_id_str) > 12:
                    raise ValueError("Track ID must not be more than 12 digits long for EAN-13 barcode.")
                else:
                    barcode_number = track_id_str

                # Generate the EAN-13 barcode
                EAN = barcode.get_barcode_class('ean13')
                ean = EAN(barcode_number, writer=ImageWriter())
                barcode_path = os.path.join(settings.MEDIA_ROOT, 'barcode', f'{track_id}.png')

                try:
                    # Save the barcode image to a file
                    with open(barcode_path, 'wb') as barcode_file:
                        ean.write(barcode_file)

                    # Save the barcode image and barcode_number in the consignment record
                    consignment.barcode_image.save(f'barcode/{track_id}.png', File(open(barcode_path, 'rb')))
                    consignment.barcode_number = barcode_number  # Save the barcode number as track_id
                    consignment.save()

                except Exception as e:
                    print(f"Error saving barcode image: {e}")
                    raise

            except Exception as e:
                logger.exception("Error generating barcode")  # Log the complete traceback
                return JsonResponse({'error': 'Error generating barcode. Please try again later.'}, status=400)

            # Account processing
            try:
                previous_balance_entry = Account.objects.filter(sender_name=send_name).order_by('-Date').first()
                previous_balance = float(previous_balance_entry.Balance) if previous_balance_entry else 0.0
                updated_balance = previous_balance + cost

                account_entry, created = Account.objects.update_or_create(
                    track_number=con_id,
                    defaults={
                        'Date': now,
                        'debit': cost,
                        'credit': 0,
                        'TrType': "sal",
                        'particulars': f"{con_id} Debited",
                        'Balance': updated_balance,
                        'sender_name': account_name,
                        'headname': username,
                        'Branch': branch_value
                    }
                )
            except (IntegrityError, ValidationError) as e:
                logger.exception("Error updating account")  # Log the complete traceback
                return JsonResponse({'error': 'Error updating account. Please check your inputs.'}, status=400)

            return JsonResponse({'success': True, 'track_id': con_id})

        except Exception as e:
            logger.exception("An unexpected error occurred")  # Log the complete traceback
            return JsonResponse({'error': 'An unexpected error occurred. Please try again later.'}, status=500)

    else:
        # Fetch categories
        cat = Category.objects.all()
        return render(request, 'addConsignment.html', {'cat': cat})

def printConsignment(request, track_id):
    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)
        uid = request.session.get('username')
        data = Staff.objects.get(staffPhone=uid)
        branch = data.Branch
        branchdetails = Branch.objects.get(companyname=branch)

        # Create a list to hold details of each consignment
        consignment_details = []
        copy_types = set()

        for consignment in consignments:
            # Ensure that 'barcode_image' is explicitly added here
            details = {
                'track_id': consignment.track_id,
                'sender_name': consignment.sender_name,
                'receiver_name': consignment.receiver_name,
                'sender_mobile': consignment.sender_mobile,
                'receiver_mobile': consignment.receiver_mobile,
                'sender_address': consignment.sender_address,
                'receiver_address': consignment.receiver_address,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'freight': consignment.freight,
                'hamali': consignment.hamali,
                'door_charge': consignment.door_charge,
                'total_cost': consignment.total_cost,
                'pay_status': consignment.pay_status,
                'pieces': consignment.pieces,
                'category': consignment.category,
                'weight': consignment.weight,
                'eway_bill': consignment.eway_bill,
                'date': consignment.date,
                'barcode_image': consignment.barcode_image  # Handle the image URL
            }
            consignment_details.append(details)

            # Collect unique copy types
            copy_types.add(consignment.copy_type)

        # Convert copy types set to a list
        copy_types_list = list(copy_types)

    except ObjectDoesNotExist:
        consignment_details = []
        copy_types_list = []
        branchdetails = None  # Handle branch details if no consignment found

    return render(request, 'printConsignment.html', {
        'consignment_details': consignment_details,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types_list)
    })



def invoiceConsignment(request, track_id):
    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)
        uid = request.session.get('username')
        branchdetails = Branch.objects.get(email=uid)

        # Create a list to hold details of each consignment
        consignment_details = []
        copy_types = set()

        for consignment in consignments:
            # Ensure that 'barcode_image' is explicitly added here
            details = {
                'track_id': consignment.track_id,
                'sender_name': consignment.sender_name,
                'receiver_name': consignment.receiver_name,
                'sender_mobile': consignment.sender_mobile,
                'receiver_mobile': consignment.receiver_mobile,
                'sender_address': consignment.sender_address,
                'receiver_address': consignment.receiver_address,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'freight': consignment.freight,
                'hamali': consignment.hamali,
                'door_charge': consignment.door_charge,
                'total_cost': consignment.total_cost,
                'pay_status': consignment.pay_status,
                'pieces': consignment.pieces,
                'category': consignment.category,
                'weight': consignment.weight,
                'eway_bill': consignment.eway_bill,
                'date': consignment.date,
                'barcode_image': consignment.barcode_image  # Handle the image URL
            }
            consignment_details.append(details)

            # Collect unique copy types
            copy_types.add(consignment.copy_type)

        # Convert copy types set to a list
        copy_types_list = list(copy_types)

    except ObjectDoesNotExist:
        consignment_details = []
        copy_types_list = []
        branchdetails = None  # Handle branch details if no consignment found

    return render(request, 'branchinvoiceConsignment.html', {
        'consignment_details': consignment_details,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types_list)
    })




def view_consignment(request):
    uid = request.session.get('username')
    consignments_list = []

    if uid:
        try:
            data = Staff.objects.get(staffPhone=uid)
            name = data.Branch
            branch = Branch.objects.get(companyname=name)
            user_branch = branch.companyname  # Adjust if the branch info is stored differently

            from_date_str = request.POST.get('from_date')
            to_date_str = request.POST.get('to_date')
            order = request.POST.get('orderno')

            # Parse dates
            from_date = parse_date(from_date_str) if from_date_str else None
            to_date = parse_date(to_date_str) if to_date_str else None

            # Fetch consignments for the branch
            consignments = AddConsignment.objects.filter(branch=user_branch)

            if order:
                consignments = consignments.filter(track_id=order)
            if from_date and to_date:
                consignments = consignments.filter(date__range=(from_date, to_date))
            elif from_date:
                consignments = consignments.filter(date__gte=from_date)
            elif to_date:
                consignments = consignments.filter(date__lte=to_date)

            # Collect details without grouping
            for consignment in consignments:
                details = {
                    'date': consignment.date,
                'track_id': consignment.track_id,
                'barcode_number': consignment.barcode_number,
                'branch': consignment.branch,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'sender_name': consignment.sender_name,
                'sender_mobile': consignment.sender_mobile,
                'sender_address': consignment.sender_address,
                'receiver_name': consignment.receiver_name,
                'receiver_mobile': consignment.receiver_mobile,
                'receiver_address': consignment.receiver_address,
                'total_cost': consignment.total_cost,
                'pieces': consignment.pieces,
                'weight': consignment.weight,
                'pay_status': consignment.pay_status,
                'remark': consignment.remark,
                'eway_bill': consignment.eway_bill,
                'category': consignment.category,  # Store product details directly
                }
                consignments_list.append(details)

        except ObjectDoesNotExist:
            pass

    return render(request, 'view_consignment.html', {'consignments_list': consignments_list})


def user_view_consignment(request):
    uid = request.session['username']
    userdata = AddConsignment.objects.filter(receiver_email=uid).values()
    return render(request,'user_view_consignment.html',{'userdata':userdata})


def consignment_edit(request, pk):
    userdata = AddConsignment.objects.filter(id=pk).first()  # Retrieve a single object or None


    if request.method == "POST":
        track_id = userdata.track_id
        con_date = userdata.date

        send_name = request.POST.get('a1')
        send_mobile = request.POST.get('a2')
        send_email = request.POST.get('a3')
        send_address = request.POST.get('a4')

        rec_name = request.POST.get('a5')
        rec_mobile = request.POST.get('a6')
        rec_email = request.POST.get('a7')
        rec_address = request.POST.get('a8')

        cost = request.POST.get('a9')

        # Update the object
        userdata.track_no = track_id
        userdata.sender_name = send_name
        userdata.sender_mobile = send_mobile
        userdata.sender_email = send_email
        userdata.sender_address = send_address
        userdata.receiver_name = rec_name
        userdata.receiver_mobile = rec_mobile
        userdata.receiver_email = rec_email
        userdata.receiver_address = rec_address
        userdata.total_cost = cost
        userdata.date = con_date
        userdata.save()

        # Redirect to a different URL after successful update
        base_url = reverse('view_consignment')
        return redirect(base_url)

    return render(request, 'consignment_edit.html', {'userdata': userdata})


def consignment_delete(request,pk):
    udata=AddConsignment.objects.get(id=pk)
    udata.delete()
    base_url=reverse('view_consignment')
    return redirect(base_url)




def addTrack(request):
    consignments = AddConsignment.objects.all().order_by('-id')  # Fetch all consignments ordered by id descending
    if request.method == "POST":
        now = datetime.datetime.now()
        con_date = now.strftime("%Y-%m-%d")

        track_id = request.POST.get('a1')
        status = request.POST.get('status')  # Retrieve status from the form

        # Retrieve total_cost from AddConsignment table based on some condition
        # For example, you can get it based on track_id or any other criteria

        # If the selected status is "Other", retrieve the custom status from the form
        if status == "Other":
            custom_status = request.POST.get('a2')
        else:
            custom_status = None

        # Create AddTrack object with retrieved total_cost
        AddTrack.objects.create(
            track_id=track_id,
            description=status,
            date=con_date

        )

        return render(request, 'addTrack.html', {'msg': 'Added'})
    return render(request, 'addTrack.html',{'consignments':consignments})


def search_results(request):
    tracker_id = request.GET.get('tracker_id')
    consignments = AddConsignment.objects.all().order_by('-id')  # Fetch all consignment data

    if tracker_id:
        try:
            trackers = AddTrack.objects.filter(track_id=tracker_id)
            if trackers.exists():
                return render(request, 'search_results.html', {'trackers': trackers, 'consignments': consignments})
            else:
                message = f"No tracking information found for ID: {tracker_id}"
                return render(request, 'search_results.html', {'message': message, 'consignments': consignments})
        except Exception as e:
            message = f"Error occurred: {str(e)}"
            return render(request, 'search_results.html', {'message': message, 'consignments': consignments})
    else:
        return render(request, 'search_results.html', {'message': "Please enter a tracker ID.", 'consignments': consignments})



def track_delete(request,pk):
    udata=AddTrack.objects.get(id=pk)
    udata.delete()
    base_url=reverse('search_results')
    return redirect(base_url)


def user_search_results(request):
    tracker_id = request.GET.get('tracker_id')

    if tracker_id:
        try:
            trackers = AddTrack.objects.filter(track_id=tracker_id)
            if trackers.exists():
                return render(request, 'user_search_results.html', {'trackers': trackers})
            else:
                message = f"No tracking information found for ID: {tracker_id}"
                return render(request, 'user_search_results.html', {'message': message})
        except Exception as e:
            message = f"Error occurred: {str(e)}"
            return render(request, 'user_search_results.html', {'message': message})
    else:
        return render(request, 'user_search_results.html', {'message': "Please enter a tracker ID."})

def branch(request):
    if request.method == "POST":
        companyname = request.POST.get('companyname')
        headname = request.POST.get('headname')
        phonenumber = request.POST.get('phonenumber')
        email = request.POST.get('email')
        password = request.POST.get('password')
        address = request.POST.get('address')

        utype = 'branch'


        if Login.objects.filter(username=email).exists():
            messages.error(request, 'Username (email) already exists.')
            return render(request, 'branch.html')

        # If the email does not exist, create the branch and login records
        Branch.objects.create(
            companyname=companyname,
            phonenumber=phonenumber,
            email=email,
            address=address,
            headname=headname,
            password=password
        )
        Login.objects.create(utype=utype, username=email, password=password, name=headname)

        messages.success(request, 'Branch created successfully.')

    return render(request, 'branch.html')




def view_branch(request):
    data=Branch.objects.all()
    return render(request,'view_branch.html',{'data':data})


def edit_branch(request, pk):
    data = Branch.objects.filter(id=pk).first()  # Retrieve a single object or None

    original_email = data.email

    if request.method == "POST":
        companyname = request.POST.get('companyname')
        headname = request.POST.get('headname')
        phonenumber = request.POST.get('phonenumber')
        email = request.POST.get('email')
        address = request.POST.get('address')
        password = request.POST.get('password')

        # Update the object
        data.companyname = companyname
        data.headname = headname
        data.phonenumber = phonenumber
        data.email = email
        data.address = address
        data.password=password
        data.save()


        # Update the Login record using the original staffPhone
        user = Login.objects.filter(username=original_email).first()  # Fetch the user with the original phone number
        if user:
            user.username = email  # Update username to the new phone number
            user.name = headname  # Update name
            user.password=password
            user.save()
        # Redirect to a different URL after successful update
        base_url = reverse('view_branch')
        return redirect(base_url)

    return render(request, 'edit_branch.html', {'data': data})

def branch_delete(request,pk):
    udata=Branch.objects.get(id=pk)
    user = Login.objects.filter(username=udata.email).first()
    if user:
        user.delete()
    udata.delete()
    base_url=reverse('view_branch')
    return redirect(base_url)

def driver(request):
    if request.method == "POST":
        driver_name = request.POST.get('driver_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        passport = request.POST.get('passport')
        license = request.POST.get('license')

        passportfile = request.FILES['passport']
        fs = FileSystemStorage()
        filepassport = fs.save(passportfile.name, passportfile)
        upload_file_url = fs.url(filepassport)
        path = os.path.join(BASE_DIR, '/media/' + filepassport)

        licensefile = request.FILES['license']
        fs = FileSystemStorage()
        filelicense= fs.save(licensefile.name, licensefile)
        upload_file_url = fs.url(filelicense)
        path = os.path.join(BASE_DIR, '/media/' + filelicense)

        Driver.objects.create(
            driver_name=driver_name,
            phone_number=phone_number,
            address=address,
            passport=passportfile,
            license=licensefile
        )
    return render(request, 'driver.html')


def view_driver(request):
    data=Driver.objects.all()
    return render(request,'view_driver.html',{'data':data})


def driver_edit(request, pk):
    data = Driver.objects.filter(id=pk).first()  # Retrieve a single object or None


    if request.method == "POST":
        driver_name = request.POST.get('driver_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        vehicle_number = request.POST.get('vehicle_number')


        # Update the object
        data.driver_name = driver_name
        data.phone_number = phone_number
        data.address = address
        data.vehicle_number = vehicle_number

        data.save()

        # Redirect to a different URL after successful update
        base_url = reverse('view_driver')
        return redirect(base_url)

    return render(request, 'driver_edit.html', {'data': data})


def driver_delete(request,pk):
    udata=Driver.objects.get(id=pk)
    udata.delete()
    base_url=reverse('view_driver')
    return redirect(base_url)


def vehicle(request):
    if request.method == "POST":
        vehicle_number = request.POST.get('vehicle_number')

        Vehicle.objects.create(
            vehicle_number=vehicle_number
        )
    return render(request, 'vehicle.html')


def view_vehicle(request):
    data=Vehicle.objects.all()
    return render(request,'view_vehicle.html',{'data':data})


def vehicle_edit(request, pk):
    data = Vehicle.objects.filter(id=pk).first()  # Retrieve a single object or None


    if request.method == "POST":
        vehicle_number = request.POST.get('vehicle_number')

        data.vehicle_number = vehicle_number

        data.save()

        # Redirect to a different URL after successful update
        base_url = reverse('view_vehicle')
        return redirect(base_url)

    return render(request, 'vehicle_edit.html', {'data': data})


def vehicle_delete(request,pk):
    udata=Vehicle.objects.get(id=pk)
    udata.delete()
    base_url=reverse('view_vehicle')
    return redirect(base_url)


def get_consignor_name(request):
    query = request.GET.get('query', '')
    if query:
        sender_names = Consignor.objects.filter(sender_name__icontains=query).values_list('sender_name', flat=True)
        print('sender_names numbers:', list(sender_names))  # Debugging: check the data in the terminal
        return JsonResponse(list(sender_names), safe=False)
    return JsonResponse([], safe=False)

def get_consignor_number(request):
    query = request.GET.get('query', '')
    if query:
        sender_mobiles = Consignor.objects.filter(sender_mobile__icontains=query).values_list('sender_mobile', flat=True)
        print('sender_mobiles numbers:', list(sender_mobiles))  # Debugging: check the data in the terminal
        return JsonResponse(list(sender_mobiles), safe=False)
    return JsonResponse([], safe=False)

def get_sender_number_details(request):
    name = request.GET.get('name', '')
    if name:
        consignor = Consignor.objects.filter(sender_mobile=name).first()
        if consignor:
            data = {
                'sender_name': consignor.sender_name,
                'sender_GST': consignor.sender_GST,
                'sender_address': consignor.sender_address,
            }
        else:
            data = {}
    else:
        data = {}

    return JsonResponse(data)

def get_consignee_number(request):
    query = request.GET.get('query', '')
    if query:
        receiver_mobiles = Consignee.objects.filter(receiver_mobile__icontains=query).values_list('receiver_mobile', flat=True)
        print('receiver_mobile numbers:', list(receiver_mobiles))  # Debugging: check the data in the terminal
        return JsonResponse(list(receiver_mobiles), safe=False)
    return JsonResponse([], safe=False)

def get_receiver_number_details(request):
    name = request.GET.get('name', '')
    if name:
        consignee = Consignee.objects.filter(receiver_mobile=name).first()
        if consignee:
            data = {
                'receiver_name': consignee.receiver_name,
                'receiver_GST': consignee.receiver_GST,
                'receiver_address': consignee.receiver_address,
            }
        else:
            data = {}
    else:
        data = {}

    return JsonResponse(data)

def get_account_name(request):
    query = request.GET.get('query', '')
    if query:
        sender_names = Account.objects.filter(sender_name__icontains=query).values_list('sender_name', flat=True).distinct()
        print('sender_names numbers:', list(sender_names))  # Debugging: check the data in the terminal
        return JsonResponse(list(sender_names), safe=False)
    return JsonResponse([], safe=False)

def get_sender_details(request):
    name = request.GET.get('name', '')
    if name:
        consignor = Consignor.objects.filter(sender_name=name).first()
        if consignor:
            data = {
                'sender_mobile': consignor.sender_mobile,
                'sender_GST': consignor.sender_GST,
                'sender_address': consignor.sender_address,
            }
        else:
            data = {}
    else:
        data = {}

    return JsonResponse(data)

def get_parties_name(request):
    query = request.GET.get('query', '')
    if query:
        sender_names = Parties.objects.filter(sender_name__icontains=query).values_list('sender_name', flat=True)
        print('sender_names numbers:', list(sender_names))  # Debugging: check the data in the terminal
        return JsonResponse(list(sender_names), safe=False)
    return JsonResponse([], safe=False)


def get_parties_details(request):
    sender_name = request.GET.get('name', None)

    if sender_name:
        try:
            # Fetch the party details based on sender_name
            party = Parties.objects.get(sender_name=sender_name)

            # Construct the response data
            data = {
                'route_from': party.route_from,
                'route_to': party.route_to,
                'sender_name': party.sender_name,
                'sender_mobile': party.sender_mobile,
                'sender_address': party.sender_address,
                'sender_GST': party.sender_GST,
                'receiver_name': party.receiver_name,
                'receiver_mobile': party.receiver_mobile,
                'receiver_address': party.receiver_address,
                'receiver_GST': party.receiver_GST,
            }

            return JsonResponse(data)
        except Parties.DoesNotExist:
            return JsonResponse({'error': 'Party not found'}, status=404)

    return JsonResponse({'error': 'No sender name provided'}, status=400)


def get_consignee_name(request):
    query = request.GET.get('query', '')
    if query:
        receiver_names = Consignee.objects.filter(receiver_name__icontains=query).values_list('receiver_name', flat=True)
        print('sender_names numbers:', list(receiver_names))  # Debugging: check the data in the terminal
        return JsonResponse(list(receiver_names), safe=False)
    return JsonResponse([], safe=False)



def get_rec_details(request):
    name = request.GET.get('name', '')
    data = {}

    if name:
        try:
            consignee = Consignee.objects.get(receiver_name=name)  # Use .get() if you expect a single result
            data = {
                'receiver_mobile': consignee.receiver_mobile,
                'receiver_GST': consignee.receiver_GST,
                'receiver_address': consignee.receiver_address,
            }
        except Consignee.DoesNotExist:
            data = {'error': 'Consignee not found'}

    return JsonResponse(data)



def branchConsignment(request):
    if request.method == "POST":
        try:
            now = datetime.now()
            con_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")

            # Get user session info
            uid = request.session.get('username')
            branch = Branch.objects.get(email=uid)
            uname = branch.companyname
            username = branch.headname

            # Get the last track_id and increment it
            last_track_id = AddConsignment.objects.aggregate(Max('track_id'))['track_id__max']
            track_id = int(last_track_id) + 1 if last_track_id else 1001
            con_id = str(track_id)

            # Get the last Consignment_id and increment it
            last_con_id = AddConsignment.objects.aggregate(Max('Consignment_id'))['Consignment_id__max']
            Consignment_id = last_con_id + 1 if last_con_id else 1001
            Consignment_id = str(Consignment_id)

            # Sender and Receiver details
            send_name = request.POST.get('a1')
            send_mobile = request.POST.get('a2')
            send_address = request.POST.get('a4')
            sender_GST = request.POST.get('sendergst')
            rec_name = request.POST.get('a5')
            rec_mobile = request.POST.get('a6')
            rec_address = request.POST.get('a8')
            rec_GST = request.POST.get('receivergst')
            route_from = request.POST.get('from')
            route_to = request.POST.get('to')

            # Validation for required fields
            if not send_name or not rec_name:
                error_message = 'Sender and Receiver names are required.'
                logger.error(error_message)  # Log error details
                return JsonResponse({'error': error_message}, status=400)

            # Check if route_to matches any location in Location model
            location_match = Location.objects.filter(location=route_to).exists()
            if not location_match:
                invalid_locations = Location.objects.values_list('location', flat=True)
                error_message = f'The destination route does not match the allowed locations: {", ".join(invalid_locations)}.'
                logger.warning(error_message)  # Log warning for invalid locations
                return JsonResponse({'error': error_message}, status=400)

            # Check if route_to matches any location in Location model
            location_from = Location.objects.filter(location=route_from).exists()
            if not location_from:
                invalid_locations = Location.objects.values_list('location', flat=True)
                error_message = f'The From route does not match the allowed locations: {", ".join(invalid_locations)}.'
                logger.warning(error_message)  # Log warning for invalid locations
                return JsonResponse({'error': error_message}, status=400)

            # Copies (consignor, consignee, etc.)
            copies = []
            if request.POST.get('consignor_copy'):
                copies.append('Consignor Copy')
            if request.POST.get('consignee_copy'):
                copies.append('Consignee Copy')
            if request.POST.get('lorry_copy'):
                copies.append('Lorry Copy')
            copy_type = ', '.join(copies)

            # Create or update Consignor
            try:
                consignor, _ = Consignor.objects.update_or_create(
                    sender_name=send_name,
                    defaults={
                        'sender_mobile': send_mobile,
                        'sender_address': send_address,
                        'sender_GST': sender_GST,
                        'branch': uname,
                        'username': username
                    }
                )
            except (IntegrityError, ValidationError) as e:
                logger.exception("Error saving consignor")  # Log the complete traceback
                return JsonResponse({'error': 'Error saving consignor. Please check your inputs.'}, status=400)

            # Create or update Consignee
            try:
                consignee, _ = Consignee.objects.update_or_create(
                    receiver_name=rec_name,
                    defaults={
                        'receiver_mobile': rec_mobile,
                        'receiver_address': rec_address,
                        'receiver_GST': rec_GST,
                        'branch': uname,
                        'username': username
                    }
                )
            except (IntegrityError, ValidationError) as e:
                logger.exception("Error saving consignee")  # Log the complete traceback
                return JsonResponse({'error': 'Error saving consignee. Please check your inputs.'}, status=400)

            # Other consignment details
            remark = request.POST.get('remark')
            delivery = request.POST.get('delivery_option')
            pieces = request.POST.get('packages')
            prod_price = request.POST.get('prod_price')
            eway_bill = request.POST.get('ewaybill_no')
            weight = request.POST.get('weight')
            category = request.POST.get('category')
            freight = float(request.POST.get('freight', 0))
            hamali = request.POST.get('hamali', 0)
            door_charge = request.POST.get('door_charge', 0)
            cgst = request.POST.get('cgst', 0)
            sgst = request.POST.get('sgst', 0)
            gst = request.POST.get('gst', 0)
            cost = float(request.POST.get('cost', 0))
            pay_status = request.POST.get('payment')

            unique_id = str(uuid.uuid4().int)[:12]
            utype = request.session.get('utype')
            branch_value = 'admin' if utype == 'admin' else uname

            # Determine the appropriate name based on pay_status
            account_name = send_name if pay_status == 'Shipper A/C' else rec_name if pay_status == 'Receiver A/C' else send_name

            # Save to AddConsignment
            try:
                consignment = AddConsignment.objects.create(
                    track_id=con_id,
                    Consignment_id=Consignment_id,
                    sender_name=send_name,
                    sender_mobile=send_mobile,
                    sender_address=send_address,
                    sender_GST=sender_GST,
                    receiver_name=rec_name,
                    receiver_mobile=rec_mobile,
                    receiver_address=rec_address,
                    receiver_GST=rec_GST,
                    pieces=pieces,
                    prod_price=prod_price,
                    category=category,
                    weight=weight,
                    freight=freight,
                    hamali=hamali,
                    door_charge=door_charge,
                    gst=gst,
                    cgst=cgst,
                    sgst=sgst,
                    route_from=route_from,
                    route_to=route_to,
                    total_cost=cost,
                    date=con_date,
                    pay_status=pay_status,
                    branch=branch_value,
                    name=username,
                    time=current_time,
                    copy_type=copy_type,
                    delivery=delivery,
                    eway_bill=eway_bill,
                    barcode_number=unique_id,
                    remark=remark,
                    status='Active',
                    reason='Consignment Added'
                )
                consignmenttemp = AddConsignmentTemp.objects.create(
                    track_id=con_id,
                    Consignment_id=Consignment_id,
                    sender_name=send_name,
                    sender_mobile=send_mobile,
                    sender_address=send_address,
                    sender_GST=sender_GST,
                    receiver_name=rec_name,
                    receiver_mobile=rec_mobile,
                    receiver_address=rec_address,
                    receiver_GST=rec_GST,
                    pieces=pieces,
                    prod_price=prod_price,
                    category=category,
                    weight=weight,
                    freight=freight,
                    hamali=hamali,
                    door_charge=door_charge,
                    gst=gst,
                    cgst=cgst,
                    sgst=sgst,
                    route_from=route_from,
                    route_to=route_to,
                    total_cost=cost,
                    date=con_date,
                    pay_status=pay_status,
                    branch=branch_value,
                    name=username,
                    time=current_time,
                    copy_type=copy_type,
                    delivery=delivery,
                    eway_bill=eway_bill,
                    barcode_number=unique_id,
                    remark=remark,
                    status='Active',
                    reason='Consignment Added'
                )
                ConsignmentHistory.objects.create(
                    track_id=con_id,
                    sender_name=send_name,
                    sender_mobile=send_mobile,
                    sender_address=send_address,
                    receiver_name=rec_name,
                    receiver_mobile=rec_mobile,
                    receiver_address=rec_address,
                    total_cost=cost,
                    date=con_date,
                    pay_status= pay_status,
                    route_from=route_from,
                    route_to=route_to,
                    pieces=pieces,
                    name=username,
                    time=current_time,
                    eway_bill=eway_bill,
                    category=category,
                    comment = 'Consignment Added'
                )

                # Convert track_id to a string
                track_id_str = str(track_id)

                # Check the length of track_id
                if len(track_id_str) < 12:
                    barcode_number = track_id_str.zfill(12)  # Ensure 12 digits for EAN-13
                elif len(track_id_str) > 12:
                    raise ValueError("Track ID must not be more than 12 digits long for EAN-13 barcode.")
                else:
                    barcode_number = track_id_str

                # Generate the EAN-13 barcode
                EAN = barcode.get_barcode_class('ean13')
                ean = EAN(barcode_number, writer=ImageWriter())
                barcode_path = os.path.join(settings.MEDIA_ROOT, 'barcode', f'{track_id}.png')

                try:
                    # Save the barcode image to a file
                    with open(barcode_path, 'wb') as barcode_file:
                        ean.write(barcode_file)

                    # Save the barcode image and barcode_number in the consignment record
                    consignment.barcode_image.save(f'barcode/{track_id}.png', File(open(barcode_path, 'rb')))
                    consignment.barcode_number = barcode_number  # Save the barcode number as track_id
                    consignment.save()

                except Exception as e:
                    print(f"Error saving barcode image: {e}")
                    raise

            except Exception as e:
                logger.exception("Error generating barcode")  # Log the complete traceback
                return JsonResponse({'error': 'Error generating barcode. Please try again later.'}, status=400)

            # Account processing
            try:
                previous_balance_entry = Account.objects.filter(sender_name=send_name).order_by('-Date').first()
                previous_balance = float(previous_balance_entry.Balance) if previous_balance_entry else 0.0
                updated_balance = previous_balance + cost

                account_entry, created = Account.objects.update_or_create(
                    track_number=con_id,
                    defaults={
                        'Date': now,
                        'debit': cost,
                        'credit': 0,
                        'TrType': "sal",
                        'particulars': f"{con_id} Debited",
                        'Balance': updated_balance,
                        'sender_name': account_name,
                        'headname': username,
                        'Branch': branch_value
                    }
                )
            except (IntegrityError, ValidationError) as e:
                logger.exception("Error updating account")  # Log the complete traceback
                return JsonResponse({'error': 'Error updating account. Please check your inputs.'}, status=400)

            return JsonResponse({'success': True, 'track_id': con_id})

        except Exception as e:
            logger.exception("An unexpected error occurred")  # Log the complete traceback
            return JsonResponse({'error': 'An unexpected error occurred. Please try again later.'}, status=500)

    else:
        # Fetch categories
        cat = Category.objects.all()
        return render(request, 'branchConsignment.html', {'cat': cat})




def scan_barcode(request):
    if request.method == "POST":
        # Get the scanned barcode value (usually track_id)
        scanned_data = request.POST.get('barcode_data')

        # Fetch consignment details using the scanned track_id
        consignment = get_object_or_404(AddConsignment, track_id=scanned_data)

        # Return the consignment details (you can return as JSON or render a template)
        response_data = {
            'track_id': consignment.track_id,
            'sender_name': consignment.sender_name,
            'receiver_name': consignment.receiver_name,
            'receiver_address': consignment.receiver_address,
            'receiver_mobile': consignment.receiver_mobile,
            'route_from': consignment.route_from,
            'route_to': consignment.route_to,
            'total_cost': consignment.total_cost,
        }

        return JsonResponse(response_data)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def consignment_details(request, track_id):
    # Fetch consignment details based on track_id
    consignment = get_object_or_404(AddConsignment, track_id=track_id)

    # Pass the consignment details to the template
    return render(request, 'consignment_details.html', {'consignment': consignment})


def branchprintConsignment(request, track_id):
    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)
        uid = request.session.get('username')
        branchdetails = Branch.objects.get(email=uid)

        # Create a list to hold details of each consignment
        consignment_details = []
        copy_types = set()

        for consignment in consignments:
            # Ensure that 'barcode_image' is explicitly added here
            details = {
                'track_id': consignment.track_id,
                'sender_name': consignment.sender_name,
                'receiver_name': consignment.receiver_name,
                'sender_mobile': consignment.sender_mobile,
                'receiver_mobile': consignment.receiver_mobile,
                'sender_address': consignment.sender_address,
                'receiver_address': consignment.receiver_address,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'freight': consignment.freight,
                'hamali': consignment.hamali,
                'door_charge': consignment.door_charge,
                'total_cost': consignment.total_cost,
                'pay_status': consignment.pay_status,
                'pieces': consignment.pieces,
                'category': consignment.category,
                'weight': consignment.weight,
                'eway_bill': consignment.eway_bill,
                'date': consignment.date,
                'barcode_image': consignment.barcode_image  # Handle the image URL
            }
            consignment_details.append(details)

            # Collect unique copy types
            copy_types.add(consignment.copy_type)

        # Convert copy types set to a list
        copy_types_list = list(copy_types)

    except ObjectDoesNotExist:
        consignment_details = []
        copy_types_list = []
        branchdetails = None  # Handle branch details if no consignment found

    return render(request, 'branchprintConsignment.html', {
        'consignment_details': consignment_details,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types_list)
    })




def branchviewConsignment(request):
    uid = request.session.get('username')
    consignments_list = []

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname  # Adjust if the branch info is stored differently

            from_date_str = request.POST.get('from_date')
            to_date_str = request.POST.get('to_date')
            order = request.POST.get('orderno')
            # Parse dates
            from_date = parse_date(from_date_str) if from_date_str else None
            to_date = parse_date(to_date_str) if to_date_str else None

            # Fetch consignments for the branch
            consignments = AddConsignment.objects.filter(branch=user_branch)

            if order:
                consignments = consignments.filter(track_id=order)
            if from_date and to_date:
                consignments = consignments.filter(date__range=(from_date, to_date))
            elif from_date:
                consignments = consignments.filter(date__gte=from_date)
            elif to_date:
                consignments = consignments.filter(date__lte=to_date)

            # Collect details without grouping
            for consignment in consignments:
                details = {
                    'date': consignment.date,
                'track_id': consignment.track_id,
                'barcode_number': consignment.barcode_number,
                'branch': consignment.branch,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'sender_name': consignment.sender_name,
                'sender_mobile': consignment.sender_mobile,
                'sender_address': consignment.sender_address,
                'receiver_name': consignment.receiver_name,
                'receiver_mobile': consignment.receiver_mobile,
                'receiver_address': consignment.receiver_address,
                'total_cost': consignment.total_cost,
                'pieces': consignment.pieces,
                'weight': consignment.weight,
                'pay_status': consignment.pay_status,
                'remark': consignment.remark,
                'eway_bill': consignment.eway_bill,
                'category': consignment.category,  # Store product details directly
                }
                consignments_list.append(details)

        except ObjectDoesNotExist:
            pass

    return render(request, 'branchviewConsignment.html', {'consignments_list': consignments_list})



def branchMaster(request):
    uid = request.session['username']
    email=Branch.objects.get(email=uid)
    bid = email.id
    data = Branch.objects.filter(id=bid).first()  # Retrieve a single object or None
    if request.method == "POST":
        companyname = request.POST.get('companyname')
        phonenumber = request.POST.get('phonenumber')
        email = request.POST.get('email')
        gst = request.POST.get('gst')
        address = request.POST.get('address')
        image= request.POST.get('image')

        # Update the object
        data.companyname = companyname
        data.phonenumber = phonenumber
        data.email = email
        data.gst = gst
        data.address = address
        data.image=image

        data.save()

        # Redirect to a different URL after successful update
        base_url = reverse('branchMaster')
        return redirect(base_url)

    return render(request, 'branchMaster.html', {'data': data})

from django.contrib import messages
from django.http import HttpResponse

def branchconsignment_edit(request, pk):
    now = datetime.now()
    con_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    uid = request.session.get('username')
    uname = Login.objects.get(username=uid)
    username = uname.name

    userdata = AddConsignment.objects.filter(track_id=pk).first()
    tempdata = AddConsignmentTemp.objects.filter(track_id=pk).first()
    history = ConsignmentHistory.objects.filter(track_id=pk)
    stages = Stages.objects.filter(LrNo=pk)
    cat = Category.objects.all()

    # Retrieve all location names
    all_locations = Location.objects.values_list('location', flat=True)

    if not userdata:
        return HttpResponse("Consignment data not found.", status=404)

    stage_names = stages.values_list('stage', flat=True)
    stage_details = Stages.objects.filter(LrNo=pk).values('stage', 'username', 'Date', 'Time', 'Branch',
                                                          'branchlocation')

    if request.method == "POST":
        post_data = request.POST
        route_from = post_data.get('from')
        route_to = post_data.get('to')

        # Check if route_from and route_to exist in the Location model
        if not Location.objects.filter(location=route_from).exists():
            # Add list of all locations to the error message
            location_list = ', '.join(all_locations)
            messages.error(request, f"Invalid route from: {route_from}. Available locations are: {location_list}")
        elif not Location.objects.filter(location=route_to).exists():
            # Add list of all locations to the error message
            location_list = ', '.join(all_locations)
            messages.error(request, f"Invalid route to: {route_to}. Available locations are: {location_list}")
        else:
            try:
                # Update userdata with form data
                userdata.route_from = route_from
                userdata.route_to = route_to
                userdata.sender_name = post_data.get('a1')
                userdata.sender_mobile = post_data.get('a2')
                userdata.sender_GST = post_data.get('a3')
                userdata.sender_address = post_data.get('a4')
                userdata.receiver_name = post_data.get('a5')
                userdata.receiver_mobile = post_data.get('a6')
                userdata.receiver_GST = post_data.get('a7')
                userdata.receiver_address = post_data.get('a8')
                userdata.total_cost = post_data.get('cost')
                userdata.weight = post_data.get('weight')
                userdata.pieces = post_data.get('packages')
                userdata.freight = post_data.get('freight')
                userdata.hamali = post_data.get('hamali')
                userdata.door_charge = post_data.get('door_charge')
                userdata.cgst = float(post_data.get('cgst', 0) or 0)
                userdata.sgst = float(post_data.get('sgst', 0) or 0)
                userdata.remark = post_data.get('remark')
                userdata.category = post_data.get('category')
                userdata.pay_status = post_data.get('payment')
                userdata.eway_bill = post_data.get('ewaybill_no')
                userdata.status = post_data.get('status')
                userdata.reason = post_data.get('reason')

                userdata.save()

                if tempdata:
                    tempdata.route_from = route_from
                    tempdata.route_to = route_to
                    tempdata.sender_name = post_data.get('a1')
                    tempdata.sender_mobile = post_data.get('a2')
                    tempdata.sender_address = post_data.get('a4')
                    tempdata.sender_location = post_data.get('send_location')
                    tempdata.receiver_name = post_data.get('a5')
                    tempdata.receiver_mobile = post_data.get('a6')
                    tempdata.receiver_address = post_data.get('a8')
                    tempdata.receiver_location = post_data.get('rec_location')
                    tempdata.total_cost = post_data.get('cost')
                    tempdata.weight = post_data.get('weight')
                    tempdata.pieces = post_data.get('packages')
                    tempdata.freight = post_data.get('freight')
                    tempdata.hamali = post_data.get('hamali')
                    tempdata.door_charge = post_data.get('door_charge')
                    tempdata.cgst = float(post_data.get('cgst', 0) or 0)
                    tempdata.sgst = float(post_data.get('sgst', 0) or 0)
                    tempdata.remark = post_data.get('remark')
                    tempdata.category = post_data.get('category')
                    tempdata.pay_status = post_data.get('payment')
                    tempdata.eway_bill = post_data.get('ewaybill_no')
                    tempdata.status = post_data.get('status')
                    tempdata.reason = post_data.get('reason')

                    tempdata.save()

                commit = post_data.get('commit')
                if commit:
                    ConsignmentHistory.objects.create(
                        track_id=pk,
                        sender_name=post_data.get('a1'),
                        sender_mobile=post_data.get('a2'),
                        sender_address=post_data.get('a4'),
                        receiver_name=post_data.get('a5'),
                        receiver_mobile=post_data.get('a6'),
                        receiver_address=post_data.get('a8'),
                        total_cost=post_data.get('cost'),
                        date=con_date,
                        pay_status=post_data.get('payment'),
                        route_from=route_from,
                        route_to=route_to,
                        pieces=post_data.get('packages'),
                        name=username,
                        time=current_time,
                        eway_bill=post_data.get('ewaybill_no'),
                        category=post_data.get('category'),
                        commit=commit
                    )

                selected_stage = post_data.get('stage')
                branchname = post_data.get('branch')
                branchadd = Branch.objects.get(companyname=branchname)
                branchlocation = branchadd.address

                if selected_stage:
                    existing_stage = Stages.objects.filter(LrNo=pk, stage=selected_stage).exists()
                    if not existing_stage:
                        Stages.objects.create(
                            Date=con_date,
                            Time=current_time,
                            LrNo=pk,
                            username=username,
                            Branch=branchname,
                            branchlocation=branchlocation,
                            stage=selected_stage
                        )

                return redirect(reverse('adminView_Consignment'))

            except ValueError as e:
                messages.error(request, f"Error: {str(e)}")

    return render(request, 'branchconsignment_edit.html', {
        'userdata': userdata,
        'cat': cat,
        'history': history,
        'stages': stages,
        'stage_names': list(stage_names),
        'stage_details': stage_details,
    })



def branchconsignment_delete(request,pk):
    udata=AddConsignment.objects.get(id=pk)
    udata.delete()
    base_url=reverse('view_consignment')
    return redirect(base_url)



def branchinvoiceConsignment(request, track_id):
    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)
        uid = request.session.get('username')
        branchdetails = Branch.objects.get(email=uid)

        # Create a list to hold details of each consignment
        consignment_details = []
        copy_types = set()

        for consignment in consignments:
            # Ensure that 'barcode_image' is explicitly added here
            details = {
                'track_id': consignment.track_id,
                'sender_name': consignment.sender_name,
                'receiver_name': consignment.receiver_name,
                'sender_mobile': consignment.sender_mobile,
                'receiver_mobile': consignment.receiver_mobile,
                'sender_address': consignment.sender_address,
                'receiver_address': consignment.receiver_address,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'freight': consignment.freight,
                'hamali': consignment.hamali,
                'door_charge': consignment.door_charge,
                'total_cost': consignment.total_cost,
                'pay_status': consignment.pay_status,
                'pieces': consignment.pieces,
                'category': consignment.category,
                'weight': consignment.weight,
                'eway_bill': consignment.eway_bill,
                'date': consignment.date,
                'barcode_image': consignment.barcode_image  # Handle the image URL
            }
            consignment_details.append(details)

            # Collect unique copy types
            copy_types.add(consignment.copy_type)

        # Convert copy types set to a list
        copy_types_list = list(copy_types)

    except ObjectDoesNotExist:
        consignment_details = []
        copy_types_list = []
        branchdetails = None  # Handle branch details if no consignment found

    return render(request, 'branchinvoiceConsignment.html', {
        'consignment_details': consignment_details,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types_list)
    })



def branchaddTrack(request):
    userid = request.session.get('username')
    userdata = Branch.objects.get(email=userid)
    uname = userdata.companyname
    consignments = AddConsignment.objects.filter(branch=uname).order_by('-id')

    if request.method == "POST":
        now = datetime.datetime.now()
        con_date = now.strftime("%Y-%m-%d")

        track_id = request.POST.get('a1')
        status = request.POST.get('status')  # Retrieve status from the form

        # Retrieve custom status if "Other" is selected
        if status == "Other":
            custom_status = request.POST.get('a2')
        else:
            custom_status = None

        # Retrieve username from session and fetch the corresponding branch
        uid = request.session.get('username')

        if uid:
                userdata = Branch.objects.get(email=uid)
                uname = userdata.companyname

                # Check utype to determine the branch value
                utype = request.session.get('utype')
                branch_value = 'admin' if utype == 'admin' else uname

                # Filter consignment data based on the branch
                consignments = AddConsignment.objects.filter(branch=uname).order_by('-id')

                # Create AddTrack object
                AddTrack.objects.create(
                    track_id=track_id,
                    description=status,
                    date=con_date,
                    branch=branch_value
                )

        else:
            # Handle the case where session data is missing
            consignments = AddConsignment.objects.none()
            return render(request, 'branchaddTrack.html', {'consignments': consignments, 'msg': 'Session data missing'})

    return render(request, 'branchaddTrack.html', {'consignments': consignments})


def branchsearch_results(request):
    tracker_id = request.GET.get('tracker_id')
    userid = request.session.get('username')
    userdata = Branch.objects.get(email=userid)
    uname = userdata.companyname
    consignments = AddConsignment.objects.filter(branch=uname).order_by('-id')

    if tracker_id:
        try:
            trackers = AddTrack.objects.filter(track_id=tracker_id)
            if trackers.exists():
                return render(request, 'branchsearch_results.html', {'trackers': trackers, 'consignments': consignments})
            else:
                message = f"No tracking information found for ID: {tracker_id}"
                return render(request, 'branchsearch_results.html', {'message': message, 'consignments': consignments})
        except Exception as e:
            message = f"Error occurred: {str(e)}"
            return render(request, 'branchsearch_results.html', {'message': message, 'consignments': consignments})
    else:
        return render(request, 'branchsearch_results.html', {'message': "Please enter a tracker ID.", 'consignments': consignments})


def branchtrack_delete(request,pk):
    udata=AddTrack.objects.get(id=pk)
    udata.delete()
    base_url=reverse('branchsearch_results')
    return redirect(base_url)


def get_vehicle_numbers(request):
    query = request.GET.get('query', '')
    if query:
        vehicle_numbers = Vehicle.objects.filter(vehicle_number__icontains=query).values_list('vehicle_number', flat=True)
        print('Vehicle numbers:', list(vehicle_numbers))  # Debugging: check the data in the terminal
        return JsonResponse(list(vehicle_numbers), safe=False)
    return JsonResponse([], safe=False)

def get_driver_name(request):
    query = request.GET.get('query', '')
    if query:
        driver_name = Driver.objects.filter(driver_name__icontains=query).values_list('driver_name', flat=True)
        print('Driver Name:', list(driver_name))  # Debugging: check the data in the terminal
        return JsonResponse(list(driver_name), safe=False)
    return JsonResponse([], safe=False)

def get_branch(request):
    query = request.GET.get('query', '')
    if query:
        companyname = Branch.objects.filter(companyname__icontains=query).values_list('companyname', flat=True)
        print('Branch Name:', list(companyname))  # Debugging: check the data in the terminal
        return JsonResponse(list(companyname), safe=False)
    return JsonResponse([], safe=False)

def get_destination(request):
    query = request.GET.get('query', '')
    if query:
        # Filter and get distinct route_to values
        route_to = AddConsignment.objects.filter(route_to__icontains=query).values_list('route_to', flat=True).distinct()
        print('Distinct route_to numbers:', list(route_to))  # Debugging: check the data in the terminal
        return JsonResponse(list(route_to), safe=False)
    return JsonResponse([], safe=False)




from collections import defaultdict

def addTripSheet(request):
    route_to = AddConsignmentTemp.objects.values_list('route_to', flat=True).distinct()
    addtrip = defaultdict(
        lambda: {'category': '', 'pieces': 0, 'receiver_name': '', 'pay_status': '', 'route_to': '', 'total_cost': '',
                 'weight': '', 'prod_price': '', 'freight': '', 'hamali': '', 'door_charge': ''}
    )
    no_data_found = False  # Flag to check if data was found

    uid = request.session.get('username')
    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname

            if request.method == 'POST':
                route_to = request.POST.get('dest')
                from_date = request.POST.get('from_date')
                to_date = request.POST.get('to_date')

                # Check if both dates are provided
                if from_date and to_date:
                    consignments = AddConsignmentTemp.objects.filter(
                        route_to=route_to,
                        date__range=[from_date, to_date],  # Filtering between the date range
                        branch=user_branch
                    )

                    if consignments.exists():
                        for consignment in consignments:
                            consignment_data = addtrip[consignment.track_id]
                            consignment_data['category'] = consignment.category
                            consignment_data['pieces'] += consignment.pieces
                            consignment_data['route_to'] = consignment.route_to
                            consignment_data['receiver_name'] = consignment.receiver_name
                            consignment_data['pay_status'] = consignment.pay_status
                            consignment_data['total_cost'] = consignment.total_cost
                            consignment_data['weight'] = consignment.weight
                            consignment_data['prod_price'] = consignment.prod_price
                            consignment_data['freight'] = consignment.freight
                            consignment_data['hamali'] = consignment.hamali
                            consignment_data['door_charge'] = consignment.door_charge
                    else:
                        no_data_found = True  # Set the flag if no data is found
                else:
                    no_data_found = True  # No date provided or invalid date range

            addtrip = [
                {
                    'track_id': track_id,
                    'category': consignment_data['category'],
                    'pieces': consignment_data['pieces'],
                    'route_to': consignment_data['route_to'],
                    'receiver_name': consignment_data['receiver_name'],
                    'pay_status': consignment_data['pay_status'],
                    'total_cost': consignment_data['total_cost'],
                    'weight': consignment_data['weight'],
                    'prod_price': consignment_data['prod_price'],
                    'freight': consignment_data['freight'],
                    'hamali': consignment_data['hamali'],
                    'door_charge': consignment_data['door_charge'],
                }
                for track_id, consignment_data in addtrip.items()
            ]

        except Branch.DoesNotExist:
            addtrip = []
            no_data_found = True  # Set the flag if the branch does not exist

    return render(request, 'addTripSheet.html', {
        'route_to': route_to,
        'trip': addtrip,
        'no_data_found': no_data_found  # Pass the flag to the template
    })

def saveTripSheetList(request):
    print("saveTripSheet function called")
    if request.method == 'POST':
        print("POST request received")  # Debugging statement


        uid = request.session.get('username')
        if uid:
            try:
                branch = Branch.objects.get(email=uid)
                branchname = branch.companyname
                username = branch.headname

                now = datetime.now()
                con_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")


                total_rows = int(request.POST.get('total_rows', 0))


                selected_rows = request.POST.getlist('selected_rows')

                for i in range(1, total_rows + 1):
                    if str(i) in selected_rows:  # Only process if the row is selected
                        track_id = request.POST.get(f'track_id_{i}')
                        pieces = request.POST.get(f'pieces_{i}')
                        category = request.POST.get(f'category_{i}')  # Underscore between category and counter
                        route_to = request.POST.get(f'route_to_{i}')
                        receiver_name = request.POST.get(f'receiver_name_{i}')
                        pay_status = request.POST.get(f'pay_status_{i}')
                        total_cost = request.POST.get(f'total_cost{i}')
                        weight = request.POST.get(f'weight{i}')
                        prod_price = request.POST.get(f'prod_price{i}')
                        freight = request.POST.get(f'freight{i}')
                        hamali = request.POST.get(f'hamali{i}')
                        door_charge = request.POST.get(f'door_charge{i}')

                        print(f"Track ID: {track_id}, Pieces: {pieces}, category: {category}, Route: {route_to}, Receiver: {receiver_name}, Pay Status: {pay_status}, total_cost:{total_cost},freight:{freight},hamali:{hamali},door_charge:{door_charge}")  # Debugging statement


                        # Save to TripSheetTemp
                        TripSheetTemp.objects.create(
                            LRno=track_id,
                            qty=pieces,
                            category=category,
                            dest=route_to,
                            consignee=receiver_name,
                            pay_status=pay_status,
                            branch=branchname,
                            username=username,
                            Date=con_date,
                            total_cost=total_cost,
                            freight=freight,
                            hamali=hamali,
                            door_charge=door_charge,
                            weight=weight,
                            prod_price=prod_price
                            )

                        # Delete from AddConsignmentTemp
                        AddConsignmentTemp.objects.filter(track_id=track_id).delete()

                        print(f"Data for Track ID {track_id} saved and deleted from AddConsignmentTemp successfully.")  # Debugging statement
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Debugging statement
        else:
            print("No username found in session.")  # Debugging statement

        return redirect('addTripSheet')  # Replace with your desired success URL

    print("Not a POST request, redirecting back to form.")  # Debugging statement
    return render(request, 'addTripSheet.html')  # Redirect back to the form if not a POST request


def addTripSheetList(request):
    addtrip = []  # Initialize an empty list to store trip details
    uid = request.session.get('username')
    no_data_found = False  # Flag to check if no data is found

    if uid:
        try:
            # Fetch the user's branch from the session
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname

            if request.method == 'POST':
                # Get the selected date from the form
                date = request.POST.get('date')

                if date:
                    # Query TripSheetTemp table based on the selected date and user's branch
                    consignments = TripSheetTemp.objects.filter(
                        Date=date,
                        branch=user_branch
                    )

                    # Check if consignments exist
                    if consignments.exists():
                        # Iterate through the results and prepare the data for the template
                        addtrip = [
                            {
                                'track_id': consignment.LRno,
                                'category': consignment.category,
                                'qty': consignment.qty,
                                'dest': consignment.dest,
                                'consignee': consignment.consignee,
                                'pay_status': consignment.pay_status,
                                'total_cost': consignment.total_cost,
                                'weight': consignment.weight,
                                'prod_price': consignment.prod_price,
                                'freight': consignment.freight,
                                'hamali': consignment.hamali,
                                'door_charge': consignment.door_charge,
                            }
                            for consignment in consignments
                        ]
                    else:
                        no_data_found = True  # Set the flag if no data is found

        except Branch.DoesNotExist:
            addtrip = []
            no_data_found = True  # Set the flag if the branch does not exist

    # Render the template with the trip data and no_data_found flag
    return render(request, 'addTripSheetList.html', {
        'trip': addtrip,
        'no_data_found': no_data_found,
    })

def saveTripSheet(request):
    print("saveTripSheet function called")

    if request.method == 'POST':
        print("POST request received")  # Debugging statement

        # Generate trip_id
        last_trip_id = TripSheetPrem.objects.aggregate(Max('trip_id'))['trip_id__max']
        trip_id = int(last_trip_id) + 1 if last_trip_id else 1000  # Start from a defined base if no entries exist
        con_id = str(trip_id)

        uid = request.session.get('username')
        if uid:
            try:
                branch = Branch.objects.get(email=uid)
                branchname = branch.companyname
                username = branch.headname

                now = datetime.now()
                con_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")

                # Get form data
                # Get form data with fallback values
                vehicle = request.POST.get('vehical') or ''
                drivername = request.POST.get('drivername') or ''
                adv = request.POST.get('advance') or 0


                total_rows = int(request.POST.get('total_rows', 0))

                for i in range(1, total_rows + 1):
                    track_id = request.POST.get(f'track_id_{i}') or ''
                    category = request.POST.get(f'category_{i}') or ''
                    qty = request.POST.get(f'qty_{i}') or 0
                    dest = request.POST.get(f'dest_{i}') or ''
                    consignee = request.POST.get(f'consignee_{i}') or ''
                    total_cost = request.POST.get(f'total_cost_{i}') or 0
                    pay_status = request.POST.get(f'pay_status_{i}') or ''
                    weight = request.POST.get(f'weight_{i}') or 0
                    prod_price = request.POST.get(f'prod_price_{i}') or 0
                    freight = request.POST.get(f'freight_{i}') or 0  # Default to 0 if None
                    hamali = request.POST.get(f'hamali_{i}') or 0
                    door_charge = request.POST.get(f'door_charge_{i}') or 0

                    # Save to TripSheetPrem
                    TripSheetPrem.objects.create(
                        LRno=track_id,
                        qty=qty,
                        category=category,
                        dest=dest,
                        consignee=consignee,
                        pay_status=pay_status,
                        VehicalNo=vehicle,
                        DriverName=drivername,
                        branch=branchname,
                        username=username,
                        Date=con_date,
                        Time=current_time,
                        AdvGiven=adv,

                        total_cost=total_cost,
                        freight=freight,
                        hamali=hamali,
                        door_charge=door_charge,
                        trip_id=con_id,
                        weight=weight,
                        prod_price=prod_price,

                    )

                    # Delete from AddConsignmentTemp
                    TripSheetTemp.objects.filter(LRno=track_id).delete()

                    print(f"Data for Track ID {track_id} saved successfully.")  # Debugging statement
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Debugging statement
        else:
            print("No username found in session.")  # Debugging statement

        return redirect('addTripSheetList')  # Replace with your desired success URL

    return render(request, 'addTripSheetList.html')  # Redirect back if not a POST request


from django.db.models import Sum, F, FloatField

def tripSheet(request):
    return render(request,'tripSheet.html')

def tripSheetList(request):
    trips = []
    total_value = 0
    total_qty = 0
    total_weight = 0
    track_number_count = 0
    grand_total = 0
    grand_price = 0
    prod_price_count = 0  # Count of trips where prod_price >= 50000

    uid = request.session.get('username')

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname
            branchaddress = branch.address

            if request.method == 'POST':
                vehicle_number = request.POST.get('vehical')
                date = request.POST.get('t3')


                # Filter trips based on VehicleNo, Date, and branch
                trips = TripSheetPrem.objects.filter(
                    VehicalNo=vehicle_number,
                    Date=date,
                    branch=user_branch
                )

                # Calculate total quantity, weight, and track number count
                total_qty = trips.aggregate(total_qty=Sum('qty'))['total_qty'] or 0
                total_weight = trips.aggregate(total_weight=Sum('weight'))['total_weight'] or 0
                track_number_count = trips.count()

                # Aggregate only the grand total from total_cost and prod_price
                grand_total = trips.aggregate(total=Sum('total_cost'))['total'] or 0
                grand_price = trips.aggregate(total=Sum('prod_price'))['total'] or 0

                # Count trips where prod_price >= 50000
                prod_price_count = trips.filter(prod_price__gte=50000).count()

                # Calculate the total value using the first row
                if trips.exists():
                    first_trip = trips.first()
                    total_ltr_value = float(
                        first_trip.LTRate * first_trip.Ltr) if first_trip.LTRate and first_trip.Ltr else 0.0
                    total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
                    total_value = total_ltr_value + total_adv_given
                else:
                    total_value = 0.0

        except Branch.DoesNotExist:
            trips = TripSheetPrem.objects.none()  # Handle case where Branch does not exist

        return render(request, 'TripSheetList.html', {
            'trips': trips,
            'total_value': total_value,
            'total_qty': total_qty,
            'total_weight': total_weight,
            'track_number_count': track_number_count,
            'grand_total': grand_total,
            'grand_price': grand_price,
            'prod_price_count': prod_price_count,  # Include count in the context
            'branchaddress': branchaddress
        })

@require_POST
def delete_trip_sheet_data(request):
    vehicle_number = request.POST.get('vehical')
    date = request.POST.get('t3')
    uid = request.session.get('username')

    print(f"Received vehicle_number: {vehicle_number}, date: {date}, uid: {uid}")

    if uid and vehicle_number and date:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname
            TripSheetTemp.objects.filter(
                VehicalNo=vehicle_number,
                Date=date,
                branch=user_branch
            ).delete()
            return JsonResponse({'status': 'success'})
        except ObjectDoesNotExist:
            print("Branch does not exist.")
            return JsonResponse({'status': 'error', 'message': 'Branch does not exist'})

    print("Invalid parameters received.")
    return JsonResponse({'status': 'error', 'message': 'Invalid parameters'})
def viewTripSheetList(request):
    grouped_trips = []
    uid = request.session.get('username')

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname

            if request.method == 'POST':
                date = request.POST.get('t3')

                if date:
                    # Group by VehicalNo and Date, and annotate with count
                    grouped_trips = (
                        TripSheetPrem.objects
                        .filter(Date=date, branch=user_branch)
                        .values('VehicalNo', 'Date')
                        .annotate(trip_count=Count('id'))
                    )

        except ObjectDoesNotExist:
            grouped_trips = []

    return render(request, 'viewTripSheetList.html', {
        'grouped_trips': grouped_trips
    })


def editTripSheetList(request):
    trips = []
    total_value = 0
    total_qty = 0
    total_weight = 0
    track_number_count = 0
    grand_total = 0
    grand_price = 0
    prod_price_count = 0  # Count of trips where prod_price >= 50000

    uid = request.session.get('username')

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname

            if request.method == 'POST':
                vehicle_number = request.POST.get('vehical')
                date_str = request.POST.get('t3')

                if date_str:
                    # Directly use date_str if it's in yyyy-mm-dd format
                    date = date_str

                    # Filter trips based on the vehicle number, date, and branch
                    trips = TripSheetPrem.objects.filter(
                        VehicalNo=vehicle_number,
                        Date=date,
                        branch=user_branch
                    )
                    # Calculate total quantity, weight, and track number count
                    total_qty = trips.aggregate(total_qty=Sum('qty'))['total_qty'] or 0
                    total_weight = trips.aggregate(total_weight=Sum('weight'))['total_weight'] or 0
                    track_number_count = trips.count()

                    # Aggregate only the grand total from total_cost and prod_price
                    grand_total = trips.aggregate(total=Sum('total_cost'))['total'] or 0
                    grand_price = trips.aggregate(total=Sum('prod_price'))['total'] or 0

                    # Count trips where prod_price >= 50000
                    prod_price_count = trips.filter(prod_price__gte=50000).count()

                    # Calculate the total value using the first row
                    if trips.exists():
                        first_trip = trips.first()
                        total_ltr_value = float(
                            first_trip.LTRate * first_trip.Ltr) if first_trip.LTRate and first_trip.Ltr else 0.0
                        total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
                        total_value = total_ltr_value + total_adv_given
                    else:
                        total_value = 0.0

        except Branch.DoesNotExist:
            trips = TripSheetPrem.objects.none()

    return render(request, 'editTripSheetList.html', {
        'trips': trips,
        'total_value': total_value,
        'total_qty': total_qty,
        'total_weight': total_weight,
        'track_number_count': track_number_count,
        'grand_total': grand_total,
        'grand_price': grand_price,
        'prod_price_count': prod_price_count,  # Include count in the context
        'branchaddress':user_branch
    })


def update_view(request):
    if request.method == "POST":
        trip_id = request.POST.get("trip_id")
        print(f"Received trip_id: {trip_id}")  # Debugging line

        # Fetch all records with the matching trip_id
        trips = TripSheetPrem.objects.filter(trip_id=trip_id)

        if trips.exists():
            print(f"Found {trips.count()} trip records to update")
            for trip in trips:

                trip.AdvGiven = request.POST.get("advgiven")
                trip.save()

            # Redirect after saving
            return redirect('viewTripSheetList')  # Replace with your success URL
        else:
            print("No trip records found")
            return render(request, 'editTripSheetList.html', {'error_message': 'No trips found with the provided trip_id.'})

    return render(request, 'editTripSheetList.html')  # Replace with your template

def printTripSheetList(request):
    trips = []
    total_value = 0
    total_qty = 0
    total_weight = 0
    track_number_count = 0
    grand_total = 0
    grand_price = 0
    prod_price_count = 0  # Count of trips where prod_price >= 50000

    uid = request.session.get('username')

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname
            branchaddress= branch.address

            if request.method == 'POST':
                vehicle_number = request.POST.get('vehical')
                date_str = request.POST.get('t3')

                if date_str:
                    # Directly use date_str if it's in yyyy-mm-dd format
                    date = date_str

                    # Filter trips based on the vehicle number, date, and branch
                    trips = TripSheetPrem.objects.filter(
                        VehicalNo=vehicle_number,
                        Date=date,
                        branch=user_branch
                    )



                    # Calculate total quantity, weight, and track number count
                    total_qty = trips.aggregate(total_qty=Sum('qty'))['total_qty'] or 0
                    total_weight = trips.aggregate(total_weight=Sum('weight'))['total_weight'] or 0
                    track_number_count = trips.count()

                    # Aggregate only the grand total from total_cost and prod_price
                    grand_total = trips.aggregate(total=Sum('total_cost'))['total'] or 0
                    grand_price = trips.aggregate(total=Sum('prod_price'))['total'] or 0

                    # Count trips where prod_price >= 50000
                    prod_price_count = trips.filter(prod_price__gte=50000).count()

                    # Calculate the total value using the first row
                    if trips.exists():
                        first_trip = trips.first()
                        total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
                        total_value = total_adv_given
                    else:
                        total_value = 0.0

        except Branch.DoesNotExist:
            trips = TripSheetPrem.objects.none()  # Handle case where Branch does not exist

    return render(request, 'printTripSheetList.html', {
        'trips': trips,
        'total_value': total_value,
        'total_qty': total_qty,
        'total_weight': total_weight,
        'track_number_count': track_number_count,
        'grand_total': grand_total,
        'grand_price': grand_price,
        'prod_price_count': prod_price_count,  # Include count in the context
        'branchaddress':branchaddress
    })



def adminTripSheet(request):
    grouped_trips = []

    if request.method == 'POST':
        vehicle_number = request.POST.get('vehical')
        branch = request.POST.get('t2')
        date = request.POST.get('t3')

        if date:
            # Group by VehicalNo and Date, and annotate with count
            grouped_trips = (
                TripSheetPrem.objects
                .filter(Date=date, VehicalNo=vehicle_number,branch=branch)
                .values('VehicalNo', 'Date','branch')
                .annotate(trip_count=Count('id'))
            )
    return render(request, 'adminTripSheet.html', {
        'grouped_trips': grouped_trips
    })


def adminPrintTripSheetList(request, vehical_no, date,branch):
    trips = []
    total_value = 0
    total_qty = 0
    total_weight = 0
    track_number_count = 0
    grand_total = 0
    grand_price = 0
    prod_price_count = 0  # Count of trips where prod_price >= 50000

    # Filter trips based on VehicleNo, Date, and branch
    trips = TripSheetPrem.objects.filter(
        VehicalNo=vehical_no,
        Date=date,
        branch=branch
    )


    # Calculate total quantity, weight, and track number count
    total_qty = trips.aggregate(total_qty=Sum('qty'))['total_qty'] or 0
    total_weight = trips.aggregate(total_weight=Sum('weight'))['total_weight'] or 0
    track_number_count = trips.count()

    # Aggregate only the grand total from total_cost and prod_price
    grand_total = trips.aggregate(total=Sum('total_cost'))['total'] or 0
    grand_price = trips.aggregate(total=Sum('prod_price'))['total'] or 0

    # Count trips where prod_price >= 50000
    prod_price_count = trips.filter(prod_price__gte=50000).count()

    # Calculate the total value using the first row
    if trips.exists():
        first_trip = trips.first()
        total_ltr_value = float(first_trip.LTRate * first_trip.Ltr) if first_trip.LTRate and first_trip.Ltr else 0.0
        total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
        total_value = total_ltr_value + total_adv_given
    else:
         total_value = 0.0

    return render(request, 'adminPrintTripSheetList.html', {
        'trips': trips,
        'total_value': total_value,
        'total_qty': total_qty,
        'total_weight': total_weight,
        'track_number_count': track_number_count,
        'grand_total': grand_total,
        'grand_price': grand_price,
        'prod_price_count': prod_price_count,  # Include count in the context
    })






def staff(request):
    if request.method == "POST":

        uid = request.session.get('username')
        branch=Branch.objects.get(email=uid)
        branchname=branch.companyname

        staff = random.randint(111111, 999999)
        staffid = str(staff)

        staffname = request.POST.get('staffname')
        staffPhone = request.POST.get('staffPhone')
        staffaddress = request.POST.get('staffaddress')
        aadhar=request.POST.get('aadhar')
        passbook = request.POST.get('passbookno')

        passport = request.POST.get('passport')
        passbookphoto = request.POST.get('passport')

        passportfile = request.FILES['passport']
        fs = FileSystemStorage()
        filepassport = fs.save(passportfile.name, passportfile)
        upload_file_url = fs.url(filepassport)
        path = os.path.join(BASE_DIR, '/media/' + filepassport)

        passbookfile = request.FILES['passbook']
        fs = FileSystemStorage()
        filepassbook = fs.save(passportfile.name, passbookfile)
        upload_file_url = fs.url(filepassbook)
        path = os.path.join(BASE_DIR, '/media/' + filepassbook)

        utype = 'staff'

        if Login.objects.filter(username=staffPhone).exists():
            messages.error(request, 'Username (Phone) already exists.')
            return render(request, 'staff.html')

        Staff.objects.create(
            staffname=staffname,
            staffPhone=staffPhone,
            staffaddress=staffaddress,
            aadhar=aadhar,
            staffid=staffid,
            Branch=branchname,
            passport=passportfile,
            passbook=passbook,
            passbookphoto=passbookfile


        )
        Login.objects.create(utype=utype, username=staffPhone, password=staffid,name=staffname)

    return render(request, 'staff.html')



def view_staff(request):
    uid = request.session.get('username')
    branch = Branch.objects.get(email=uid)
    branchname = branch.companyname
    name = request.POST.get('name', '')
    if branch:
        # Filter staff data based on the branch name (case-insensitive search)
        staff_data = Staff.objects.filter(staffname__icontains=name,Branch=branchname)
    else:
        staff_data=Staff.objects.filter(Branch=branchname)
    return render(request,'view_staff.html',{'data':staff_data})

def get_staff(request):
    query = request.GET.get('query', '')
    if query:
        staffname = Staff.objects.filter(staffname__icontains=query).values_list('staffname', flat=True)
        print('Staff Name:', list(staffname))  # Debugging: check the data in the terminal
        return JsonResponse(list(staffname), safe=False)
    return JsonResponse([], safe=False)

def delete_staff(request, pk):
    try:
        staff = Staff.objects.get(id=pk)

        user = Login.objects.filter(username=staff.staffPhone).first()
        if user:
            user.delete()
        staff.delete()

    except ObjectDoesNotExist:
        pass
    base_url = reverse('view_staff')
    return redirect(base_url)

def edit_staff(request, pk):
    # Retrieve the Staff record
    data = Staff.objects.filter(id=pk).first()  # Retrieve a single object or None

    if not data:
        return HttpResponse("Staff record not found.", status=404)

    # Store the original staffPhone
    original_staffPhone = data.staffPhone

    if request.method == "POST":
        # Get updated values from the POST request
        staffname = request.POST.get('staffname')
        staffPhone = request.POST.get('staffPhone')
        staffaddress = request.POST.get('staffaddress')
        aadhar = request.POST.get('aadhar')
        staffid = request.POST.get('staffid')

        # Update the Staff object
        data.staffname = staffname
        data.staffPhone = staffPhone
        data.staffaddress = staffaddress
        data.aadhar = aadhar
        data.staffid = staffid
        data.save()

        # Update the Login record using the original staffPhone
        user = Login.objects.filter(username=original_staffPhone).first()  # Fetch the user with the original phone number
        if user:
            user.username = staffPhone  # Update username to the new phone number
            user.name = staffname  # Update name
            user.password = staffid  # Update password if necessary
            user.save()

        # Redirect to a different URL after successful update
        base_url = reverse('view_staff')
        return redirect(base_url)

    return render(request, 'edit_staff.html', {'data': data})

def staffAddTripSheet(request):
    route_to = AddConsignmentTemp.objects.values_list('route_to', flat=True).distinct()
    addtrip = defaultdict(
        lambda: {'category': '', 'pieces': 0, 'receiver_name': '', 'pay_status': '', 'route_to': '', 'total_cost': '',
                 'weight': '', 'prod_price': '', 'freight': '', 'hamali': '', 'door_charge': ''}
    )
    no_data_found = False  # Flag to check if data was found

    uid = request.session.get('username')
    if uid:
        try:
            branch = Staff.objects.get(staffPhone=uid)
            user_branch = branch.Branch

            if request.method == 'POST':
                route_to = request.POST.get('dest')
                from_date = request.POST.get('from_date')
                to_date = request.POST.get('to_date')

                # Check if both from_date and to_date are provided
                if from_date and to_date:
                    consignments = AddConsignmentTemp.objects.filter(
                        route_to=route_to,
                        date__range=[from_date, to_date],  # Filter consignments by date range
                        branch=user_branch
                    )

                    if consignments.exists():
                        for consignment in consignments:
                            consignment_data = addtrip[consignment.track_id]
                            consignment_data['category'] = consignment.category
                            consignment_data['pieces'] += consignment.pieces
                            consignment_data['route_to'] = consignment.route_to
                            consignment_data['receiver_name'] = consignment.receiver_name
                            consignment_data['pay_status'] = consignment.pay_status
                            consignment_data['total_cost'] = consignment.total_cost
                            consignment_data['weight'] = consignment.weight
                            consignment_data['prod_price'] = consignment.prod_price
                            consignment_data['freight'] = consignment.freight
                            consignment_data['hamali'] = consignment.hamali
                            consignment_data['door_charge'] = consignment.door_charge
                    else:
                        no_data_found = True  # No consignments found

            addtrip = [
                {
                    'track_id': track_id,
                    'category': consignment_data['category'],
                    'pieces': consignment_data['pieces'],
                    'route_to': consignment_data['route_to'],
                    'receiver_name': consignment_data['receiver_name'],
                    'pay_status': consignment_data['pay_status'],
                    'total_cost': consignment_data['total_cost'],
                    'weight': consignment_data['weight'],
                    'prod_price': consignment_data['prod_price'],
                    'freight': consignment_data['freight'],
                    'hamali': consignment_data['hamali'],
                    'door_charge': consignment_data['door_charge'],
                }
                for track_id, consignment_data in addtrip.items()
            ]

        except Branch.DoesNotExist:
            addtrip = []
            no_data_found = True  # Branch does not exist

    return render(request, 'staffAddTripSheet.html', {
        'route_to': route_to,
        'trip': addtrip,
        'no_data_found': no_data_found  # Pass the flag to the template
    })

def staffAddTripSheetList(request):
    addtrip = []  # Initialize an empty list to store trip details
    uid = request.session.get('username')
    no_data_found = False  # Flag to check if no data is found

    if uid:
        try:
            branch = Staff.objects.get(staffPhone=uid)
            user_branch = branch.Branch

            if request.method == 'POST':
                # Get the selected date from the form
                date = request.POST.get('date')

                if date:
                    # Query TripSheetTemp table based on the selected date and user's branch
                    consignments = TripSheetTemp.objects.filter(
                        Date=date,
                        branch=user_branch
                    )

                    # Check if consignments exist
                    if consignments.exists():
                        # Iterate through the results and prepare the data for the template
                        addtrip = [
                            {
                                'track_id': consignment.LRno,
                                'category': consignment.category,
                                'qty': consignment.qty,
                                'dest': consignment.dest,
                                'consignee': consignment.consignee,
                                'pay_status': consignment.pay_status,
                                'total_cost': consignment.total_cost,
                                'weight': consignment.weight,
                                'prod_price': consignment.prod_price,
                                'freight': consignment.freight,
                                'hamali': consignment.hamali,
                                'door_charge': consignment.door_charge,
                            }
                            for consignment in consignments
                        ]
                    else:
                        no_data_found = True  # Set the flag if no data is found

        except Branch.DoesNotExist:
            addtrip = []
            no_data_found = True  # Set the flag if the branch does not exist

        # Render the template with the trip data and no_data_found flag
        return render(request, 'staffAddTripSheetList.html', {
            'trip': addtrip,
            'no_data_found': no_data_found,
        })

def staffsaveTripSheetList(request):
    print("staffsaveTripSheetList function called")
    if request.method == 'POST':
        print("POST request received")  # Debugging statement


        uid = request.session.get('username')
        if uid:
            try:
                branch = Staff.objects.get(staffPhone=uid)
                branchname = branch.Branch
                username = branch.staffname

                now = datetime.now()
                con_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")

                total_rows = int(request.POST.get('total_rows', 0))

                selected_rows = request.POST.getlist('selected_rows')

                for i in range(1, total_rows + 1):
                    if str(i) in selected_rows:  # Only process if the row is selected
                        track_id = request.POST.get(f'track_id_{i}')
                        pieces = request.POST.get(f'pieces_{i}')
                        category = request.POST.get(f'category_{i}')
                        route_to = request.POST.get(f'route_to_{i}')
                        receiver_name = request.POST.get(f'receiver_name_{i}')
                        pay_status = request.POST.get(f'pay_status_{i}')
                        total_cost = request.POST.get(f'total_cost{i}')
                        weight = request.POST.get(f'weight{i}')
                        prod_price = request.POST.get(f'prod_price{i}')
                        freight = request.POST.get(f'freight{i}')
                        hamali = request.POST.get(f'hamali{i}')
                        door_charge = request.POST.get(f'door_charge{i}')

                        print(
                            f"Track ID: {track_id}, Pieces: {pieces}, category: {category}, Route: {route_to}, Receiver: {receiver_name}, Pay Status: {pay_status}, total_cost:{total_cost},,freight:{freight},hamali:{hamali},door_charge:{door_charge}")  # Debugging statement

                        # Save to TripSheetTemp
                        TripSheetTemp.objects.create(
                            LRno=track_id,
                            qty=pieces,
                            category=category,
                            dest=route_to,
                            consignee=receiver_name,
                            pay_status=pay_status,
                            branch=branchname,
                            username=username,
                            Date=con_date,
                            total_cost=total_cost,
                            freight=freight,
                            hamali=hamali,
                            door_charge=door_charge,
                            weight=weight,
                            prod_price=prod_price
                        )

                        # Delete from AddConsignmentTemp
                        AddConsignmentTemp.objects.filter(track_id=track_id).delete()

                        print(f"Data for Track ID {track_id} saved and deleted from AddConsignmentTemp successfully.")  # Debugging statement
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Debugging statement
        else:
            print("No username found in session.")  # Debugging statement

        return redirect('staffAddTripSheet')  # Replace with your desired success URL

    print("Not a POST request, redirecting back to form.")  # Debugging statement
    return render(request, 'staffAddTripSheet.html')  # Redirect back to the form if not a POST request


def staffSaveTripSheet(request):
    print("staffSaveTripSheet function called")
    if request.method == 'POST':
        print("POST request received")  # Debugging statement

        last_trip_id = TripSheetPrem.objects.aggregate(Max('trip_id'))['trip_id__max']
        trip_id = int(last_trip_id) + 1 if last_trip_id else 1000  # Start from a defined base if no entries exist
        con_id = str(trip_id)

        uid = request.session.get('username')
        if uid:
            try:
                branch = Staff.objects.get(staffPhone=uid)
                branchname = branch.Branch
                username = branch.staffname

                now = datetime.now()
                con_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")

                # Get form data
                # Get form data with fallback values
                vehicle = request.POST.get('vehical') or ''
                drivername = request.POST.get('drivername') or ''
                adv = request.POST.get('advance') or 0


                total_rows = int(request.POST.get('total_rows', 0))

                for i in range(1, total_rows + 1):
                    track_id = request.POST.get(f'track_id_{i}') or ''
                    category = request.POST.get(f'category_{i}') or ''
                    qty = request.POST.get(f'qty_{i}') or 0
                    dest = request.POST.get(f'dest_{i}') or ''
                    consignee = request.POST.get(f'consignee_{i}') or ''
                    total_cost = request.POST.get(f'total_cost_{i}') or 0
                    pay_status = request.POST.get(f'pay_status_{i}') or ''
                    weight = request.POST.get(f'weight_{i}', '0')
                    prod_price = request.POST.get(f'prod_price_{i}', '0')
                    freight = request.POST.get(f'freight_{i}') or 0  # Default to 0 if None
                    hamali = request.POST.get(f'hamali_{i}') or 0
                    door_charge = request.POST.get(f'door_charge_{i}') or 0

                    # Save to TripSheetPrem
                    TripSheetPrem.objects.create(
                        LRno=track_id,
                        qty=qty,
                        category=category,
                        dest=dest,
                        consignee=consignee,
                        pay_status=pay_status,
                        VehicalNo=vehicle,
                        DriverName=drivername,
                        branch=branchname,
                        username=username,
                        Date=con_date,
                        Time=current_time,
                        AdvGiven=adv,

                        total_cost=total_cost,
                        freight=freight,
                        hamali=hamali,
                        door_charge=door_charge,
                        trip_id=con_id,
                        weight=weight,
                        prod_price=prod_price,

                    )

                    # Delete from AddConsignmentTemp
                    TripSheetTemp.objects.filter(LRno=track_id).delete()

                    print(f"Data for Track ID {track_id} saved and deleted from AddConsignmentTemp successfully.")  # Debugging statement


            except Staff.DoesNotExist:
                print("Staff does not exist.")  # Debugging statement
        else:
            print("No username found in session.")  # Debugging statement

        return redirect('staffAddTripSheet')  # Replace with your desired success URL

    print("Not a POST request, redirecting back to form.")  # Debugging statement
    return render(request, 'staffAddTripSheetList.html')  # Redirect back to the form if not a POST request

def staffTripSheet(request):
    return render(request,'staffTripSheet.html')

def staffTripSheetList(request):
    trips = []
    total_value = 0
    total_qty = 0
    total_weight = 0
    track_number_count = 0
    grand_total = 0
    grand_price = 0
    prod_price_count = 0  # Count of trips where prod_price >= 50000

    uid = request.session.get('username')

    if uid:
        try:
            branch = Staff.objects.get(staffPhone=uid)
            user_branch = branch.Branch
            branch1 = Branch.objects.get(companyname=user_branch)
            branchaddress = branch1.address

            if request.method == 'POST':
                vehicle_number = request.POST.get('vehical')
                date = request.POST.get('t3')

                # Filter trips based on VehicleNo, Date, and branch
                trips = TripSheetPrem.objects.filter(
                    VehicalNo=vehicle_number,
                    Date=date,
                    branch=user_branch
                )

                # Calculate total quantity, weight, and track number count
                total_qty = trips.aggregate(total_qty=Sum('qty'))['total_qty'] or 0
                total_weight = trips.aggregate(total_weight=Sum('weight'))['total_weight'] or 0
                track_number_count = trips.count()

                # Aggregate only the grand total from total_cost and prod_price
                grand_total = trips.aggregate(total=Sum('total_cost'))['total'] or 0
                grand_price = trips.aggregate(total=Sum('prod_price'))['total'] or 0

                # Count trips where prod_price >= 50000
                prod_price_count = trips.filter(prod_price__gte=50000).count()

                # Calculate the total value using the first row
                if trips.exists():
                    first_trip = trips.first()
                    total_ltr_value = float(
                        first_trip.LTRate * first_trip.Ltr) if first_trip.LTRate and first_trip.Ltr else 0.0
                    total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
                    total_value = total_ltr_value + total_adv_given
                else:
                    total_value = 0.0

        except Branch.DoesNotExist:
            trips = TripSheetPrem.objects.none()  # Handle case where Branch does not exist

        return render(request, 'staffTripSheetList.html', {
            'trips': trips,
            'total_value': total_value,
            'total_qty': total_qty,
            'total_weight': total_weight,
            'track_number_count': track_number_count,
            'grand_total': grand_total,
            'grand_price': grand_price,
            'prod_price_count': prod_price_count,  # Include count in the context
            'branchaddress': branchaddress
        })

def staffViewTripSheetList(request):
    grouped_trips = []
    uid = request.session.get('username')

    if uid:
        try:
            branch = Staff.objects.get(staffPhone=uid)
            user_branch = branch.Branch

            if request.method == 'POST':
                date = request.POST.get('t3')

                if date:
                    # Group by VehicalNo and Date, and annotate with count
                    grouped_trips = (
                        TripSheetPrem.objects
                        .filter(Date=date, branch=user_branch)
                        .values('VehicalNo', 'Date')
                        .annotate(trip_count=Count('id'))
                    )

        except ObjectDoesNotExist:
            grouped_trips = []

    return render(request, 'staffViewTripSheetList.html', {
        'grouped_trips': grouped_trips
    })

def staffprintTripSheetList(request):
    trips = []
    total_value = 0
    total_qty = 0
    total_weight = 0
    track_number_count = 0
    grand_total = 0
    grand_price = 0
    prod_price_count = 0  # Count of trips where prod_price >= 50000

    uid = request.session.get('username')

    if uid:
        try:
            branch = Staff.objects.get(staffPhone=uid)
            user_branch = branch.Branch
            branch1 = Branch.objects.get(companyname=user_branch)
            branchaddress = branch1.address

            if request.method == 'POST':
                vehicle_number = request.POST.get('vehical')
                date_str = request.POST.get('t3')

                if date_str:
                    # Directly use date_str if it's in yyyy-mm-dd format
                    date = date_str

                    # Filter trips based on the vehicle number, date, and branch
                    trips = TripSheetPrem.objects.filter(
                        VehicalNo=vehicle_number,
                        Date=date,
                        branch=user_branch
                    )

                    # Calculate total quantity, weight, and track number count
                    total_qty = trips.aggregate(total_qty=Sum('qty'))['total_qty'] or 0
                    total_weight = trips.aggregate(total_weight=Sum('weight'))['total_weight'] or 0
                    track_number_count = trips.count()

                    # Aggregate only the grand total from total_cost and prod_price
                    grand_total = trips.aggregate(total=Sum('total_cost'))['total'] or 0
                    grand_price = trips.aggregate(total=Sum('prod_price'))['total'] or 0

                    # Count trips where prod_price >= 50000
                    prod_price_count = trips.filter(prod_price__gte=50000).count()

                    # Calculate the total value using the first row
                    if trips.exists():
                        first_trip = trips.first()

                        total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
                        total_value =  total_adv_given
                    else:
                        total_value = 0.0

        except Branch.DoesNotExist:
            trips = TripSheetPrem.objects.none()  # Handle case where Branch does not exist

        return render(request, 'staffprintTripSheetList.html', {
            'trips': trips,
            'total_value': total_value,
            'total_qty': total_qty,
            'total_weight': total_weight,
            'track_number_count': track_number_count,
            'grand_total': grand_total,
            'grand_price': grand_price,
            'prod_price_count': prod_price_count,  # Include count in the context
            'branchaddress': branchaddress
        })





def fetch_consignments(request):
    consignments = AddConsignment.objects.all()
    consignments_data = [
        {
            'id': consignment.id,
            'track_id': consignment.track_id,
            'sender_name': consignment.sender_name,
            'receiver_name': consignment.receiver_name,
        }
        for consignment in consignments
    ]
    return JsonResponse(consignments_data, safe=False)


def fetch_details(request):
    uid = request.session.get('username')

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    pay_status = request.GET.get('pay_status')
    consignor_id = request.GET.get('consignor_id')
    consignee_id = request.GET.get('consignee_id')

    # Initialize an empty list for data
    data = []

    if uid:
        try:
            # Fetch the branch of the logged-in user
            branch = Staff.objects.get(staffPhone=uid).Branch

            # Start with filtering consignments by branch
            consignments = AddConsignment.objects.filter(branch=branch)

            # Further filter consignments based on the provided parameters
            if consignor_id:
                consignments = consignments.filter(sender_name__icontains=consignor_id)
            if consignee_id:
                consignments = consignments.filter(receiver_name__icontains=consignee_id)
            if from_date and to_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                consignments = consignments.filter(date__range=(from_date, to_date))

            # Handle pay_status filtering
            if pay_status and pay_status != 'all':
                consignments = consignments.filter(pay_status__icontains=pay_status)

            # Prepare the data for JSON response without grouping
            data = [
                {
                    'track_id': consignment.track_id,
                    'sender_name': consignment.sender_name,
                    'receiver_name': consignment.receiver_name,
                    'category': consignment.category,
                    'pay_status': consignment.pay_status,
                    'pieces': consignment.pieces,
                    'total_cost': consignment.total_cost,
                }
                for consignment in consignments
            ]

        except Staff.DoesNotExist:
            print("Staff does not exist for the provided uid.")  # Handle case where Staff does not exist

    return JsonResponse({'data': data})



def branchfetch_details(request):
    uid = request.session.get('username')

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    pay_status = request.GET.get('pay_status')
    consignor_id = request.GET.get('consignor_id')
    consignee_id = request.GET.get('consignee_id')

    # Initialize an empty list for data
    data = []

    if uid:
        try:
            # Fetch the branch of the logged-in user
            branch = Branch.objects.get(email=uid)
            uname = branch.companyname

            # Start with filtering consignments by branch
            consignments = AddConsignment.objects.filter(branch=uname)

            # Further filter consignments based on the provided parameters
            if consignor_id:
                consignments = consignments.filter(sender_name__icontains=consignor_id)
            if consignee_id:
                consignments = consignments.filter(receiver_name__icontains=consignee_id)
            if from_date and to_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                consignments = consignments.filter(date__range=(from_date, to_date))
            if pay_status and pay_status != 'all':
                consignments = consignments.filter(pay_status__icontains=pay_status)

            # Prepare the data for JSON response without grouping
            data = [
                {
                    'track_id': consignment.track_id,
                    'sender_name': consignment.sender_name,
                    'receiver_name': consignment.receiver_name,
                    'category': consignment.category,
                    'pay_status': consignment.pay_status,
                    'pieces': consignment.pieces,
                    'total_cost': consignment.total_cost,
                }
                for consignment in consignments
            ]

        except Branch.DoesNotExist:
            print("Branch does not exist for the provided uid.")  # Handle case where Branch does not exist

    # Include the uid in the response data
    return JsonResponse({'uid': uid, 'data': data})


def payment_history(request):
    return render(request, 'payment_history.html')

def credit(request):
    credit = Account.objects.all()
    return render(request, 'credit.html', {'credit': credit})

@csrf_exempt
def fetch_balance(request):
    uid = request.session.get('username')

    if uid:
        try:
            # Fetch the branch of the logged-in user
            branch = Staff.objects.get(staffPhone=uid).Branch

            if request.method == 'GET':
                sender_name = request.GET.get('sender_name')
                if sender_name:
                    # Filter accounts by sender_name and branch
                    accounts = Account.objects.filter(sender_name=sender_name, Branch=branch)
                    if accounts.exists():
                        latest_account = accounts.latest('Date')  # Get the latest record by date
                        return JsonResponse({'balance': latest_account.Balance})
                    return JsonResponse({'balance': '0'})  # Default if no records found
                return JsonResponse({'status': 'error', 'message': 'Sender name is required'})
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
        except Branch.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Branch does not exist for this user'})


@csrf_exempt
def submit_credit(request):
    if request.method == 'POST':
        uid = request.session.get('username')

        consignor_name = request.POST.get('consignor_name')
        credit_amount = request.POST.get('credit_amount')
        now = datetime.now()
        if consignor_name and credit_amount:
            try:

                branch = Staff.objects.get(staffPhone=uid)
                username = branch.staffname
                branchname=branch.Branch
                # Fetch all matching records
                accounts = Account.objects.filter(sender_name=consignor_name)

                if accounts.exists():
                    # Get the latest account for calculating the new balance
                    latest_account = accounts.latest('Date')  # Assuming you want to get the latest record

                    # Calculate the new balance
                    new_balance = float(latest_account.Balance) - float(credit_amount)

                    # Create a new record with updated balance
                    new_account = Account(
                        sender_name=consignor_name,
                        credit=credit_amount,
                        debit='0',
                        TrType="ReCap",
                        particulars="Credited",# Set debit to zero
                        Balance=str(new_balance),  # Set the new balance
                        Date=now,  # Use the date of the latest record or set to current date
                        headname=username,
                        Branch=branchname
                    )
                    new_account.save()

                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No account found with the given sender name'})

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        return JsonResponse({'status': 'error', 'message': 'Invalid data'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



def credit_print(request):
    credit = Account.objects.all()
    return render(request, 'credit_print.html', {'credit': credit})




@csrf_exempt
def branchfetch_balance(request):
    uid = request.session.get('username')

    if uid:
        try:
            # Fetch the branch of the logged-in user
            branch = Branch.objects.get(email=uid).companyname

            if request.method == 'GET':
                sender_name = request.GET.get('sender_name')
                if sender_name:
                    # Filter accounts by sender_name and branch
                    accounts = Account.objects.filter(sender_name=sender_name, Branch=branch)
                    if accounts.exists():
                        latest_account = accounts.latest('Date')  # Get the latest record by date
                        return JsonResponse({'balance': latest_account.Balance})
                    return JsonResponse({'balance': '0'})  # Default if no records found
                return JsonResponse({'status': 'error', 'message': 'Sender name is required'})
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
        except Branch.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Branch does not exist for this user'})

def branchPaymenyHistory(request):
    return render(request,'branchPaymenyHistory.html')

def branchcredit(request):
    credit = Account.objects.all()
    return render(request, 'branchcredit.html', {'credit': credit})

import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def branchsubmit_credit(request):
    if request.method == 'POST':
        uid = request.session.get('username')

        consignor_name = request.POST.get('consignor_name')
        credit_amount = request.POST.get('credit_amount')
        now = datetime.now()
        if consignor_name and credit_amount:
            try:

                branch = Branch.objects.get(email=uid)
                username = branch.headname
                branchcompany =branch.companyname
                # Fetch all matching records
                accounts = Account.objects.filter(sender_name=consignor_name)

                if accounts.exists():
                    # Get the latest account for calculating the new balance
                    latest_account = accounts.latest('Date')  # Assuming you want to get the latest record

                    # Calculate the new balance
                    new_balance = float(latest_account.Balance) - float(credit_amount)

                    # Create a new record with updated balance
                    new_account = Account(
                        sender_name=consignor_name,
                        credit=credit_amount,
                        debit='0',
                        TrType="ReCap",
                        particulars="Credited",# Set debit to zero
                        Balance=str(new_balance),  # Set the new balance
                        Date=now,  # Use the date of the latest record or set to current date
                        headname=username,
                        Branch=branchcompany
                    )
                    new_account.save()

                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No account found with the given sender name'})

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        return JsonResponse({'status': 'error', 'message': 'Invalid data'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



def branchcredit_print(request):
    credit = Account.objects.all()
    return render(request, 'branchcredit_print.html', {'credit': credit})

def staffcredit_print(request):
    credit = Account.objects.all()
    return render(request, 'staffcredit_print.html', {'credit': credit})

# Set up logging
import logging

logger = logging.getLogger(__name__)

def branchfetch_account_details(request):
    if request.method == 'POST':
        uid = request.session.get('username')

        sender_name = request.POST.get('sender_name')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')

        logger.info(f"Received request with sender_name: {sender_name}, from_date: {from_date}, to_date: {to_date}")

        # Check if the required parameters are provided
        if sender_name and from_date and to_date:
            try:
                branch = Branch.objects.get(email=uid).companyname

                # Convert from_date and to_date to proper datetime objects
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()

                # Ensure the end date includes the entire day
                to_date_end = to_date + timedelta(days=1)

                # Fetch all accounts based on sender_name, branch, and date range
                accounts = Account.objects.filter(
                    sender_name=sender_name,
                    Branch=branch,
                    Date__gte=from_date,
                    Date__lt=to_date_end
                ).values(
                    'Date', 'track_number', 'TrType', 'particulars', 'debit', 'credit', 'Balance'
                ).order_by('Date')  # Order by date if needed

                logger.info(f"Fetched accounts: {list(accounts)}")

                return render(request, 'branchcredit_print.html', {
                    'accounts': accounts,
                    'sender_name': sender_name,
                    'from_date_str': from_date,
                    'to_date_str': to_date,
                    'branch': branch
                })

            except ValueError:
                logger.error("Invalid date format")
                return render(request, 'branchcredit_print.html', {'error': 'Invalid date format'})

    logger.error("Missing required parameters")
    return render(request, 'branchcredit_print.html', {'error': 'Missing required parameters'})



logger = logging.getLogger(__name__)

@csrf_exempt
def fetch_account_details(request):
    if request.method == 'POST':

        uid = request.session.get('username')

        sender_name = request.POST.get('sender_name')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')

        logger.info(f"Received request with sender_name: {sender_name}, from_date: {from_date}, to_date: {to_date}")

        # Check if the required parameters are provided
        if sender_name and from_date and to_date:
            try:
                branch = Staff.objects.get(staffPhone=uid).Branch

                # Convert from_date and to_date to proper datetime objects
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()

                # Ensure the end date includes the entire day
                to_date_end = to_date + timedelta(days=1)

                # Fetch all accounts based on sender_name, branch, and date range
                accounts = Account.objects.filter(
                    sender_name=sender_name,
                    Branch=branch,
                    Date__gte=from_date,
                    Date__lt=to_date_end
                ).values(
                    'Date', 'track_number', 'TrType', 'particulars', 'debit', 'credit', 'Balance'
                ).order_by('Date')  # Order by date if needed

                logger.info(f"Fetched accounts: {list(accounts)}")

                return render(request, 'staffcredit_print.html', {
                    'accounts': accounts,
                    'sender_name': sender_name,
                    'from_date_str': from_date,
                    'to_date_str': to_date,
                    'branch': branch
                })

            except ValueError:
                logger.error("Invalid date format")
                return render(request, 'staffcredit_print.html', {'error': 'Invalid date format'})

    logger.error("Missing required parameters")
    return render(request, 'staffcredit_print.html', {'error': 'Missing required parameters'})



def branchExpenses(request):
    return render(request, 'branchExpenses.html')
def savebranchExpenses(request):
    if request.method == 'POST':
        uid = request.session.get('username')
        if uid:
            try:
                branch = Branch.objects.get(email=uid)
                branchname = branch.companyname
                username = branch.headname

                # Parse and validate date
                date_str = request.POST.get('date')
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    print("Invalid date format.")  # Debugging statement
                    return redirect('branchExpenses')

                # Parse and validate amount
                amount = request.POST.get('amt')
                reason = request.POST.get('reason')


                Expenses.objects.create(
                    Date=date,
                    Reason=reason,
                    Amount=amount,

                    username=username,
                    branch=branchname
                )
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Debugging statement
        else:
            print("No username found in session.")  # Debugging statement

        return redirect('branchExpenses')  # Replace with your desired success URL

    return render(request, 'branchExpenses.html')


def branchViewExpenses(request):
    expenses = []
    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')

        uid = request.session.get('username')
        if uid:
            try:
                branch = Branch.objects.get(email=uid)  # Get the branch for the logged-in user
                branch_name = branch.companyname  # Assuming companyname is used as the branch identifier

                if from_date_str and to_date_str:
                    try:
                        # Parse the date strings into datetime objects
                        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

                        # Fetch expenses within the specified date range and for the logged-in branch
                        expenses = Expenses.objects.filter(
                            Date__range=(from_date, to_date),
                            branch=branch_name
                        )

                    except ValueError:
                        print("Invalid date format.")  # Handle invalid date formats
                else:
                    print("Both from_date and to_date are required.")
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Handle the case where the branch is not found

    return render(request, 'branchViewExpenses.html', {'expenses': expenses})

def adminExpenses(request):
    return render(request, 'adminExpenses.html')
def saveadminExpenses(request):
    if request.method == 'POST':
        uid = request.session.get('username')
        if uid:
            try:
                branch = Login.objects.get(username=uid)
                branchname = branch.utype
                username = branch.name

                # Parse and validate date
                date_str = request.POST.get('date')
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    print("Invalid date format.")  # Debugging statement
                    return redirect('adminExpenses')

                amount = request.POST.get('amt')
                reason = request.POST.get('reason')
                salaryDetails=request.POST.get('salaryDetails')

                Expenses.objects.create(
                    Date=date,
                    Reason=reason,
                    Amount=amount,
                    staffname=salaryDetails,
                    username=username,
                    branch=branchname
                )
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Debugging statement
        else:
            print("No username found in session.")  # Debugging statement

        return redirect('adminExpenses')  # Replace with your desired success URL

    return render(request, 'adminExpenses.html')

def adminViewExpenses(request):
    expenses = []
    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')
        branch = request.POST.get('t2')

        if from_date_str and to_date_str:
            try:
                # Parse the date strings into datetime objects
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

                # Check if branch is 'admin', fetch all expenses; otherwise, filter by branch
                if branch.lower() == 'admin':
                    # Fetch expenses within the specified date range, regardless of branch
                    expenses = Expenses.objects.filter(Date__range=(from_date, to_date))
                else:
                    # Fetch expenses within the specified date range for the specified branch
                    expenses = Expenses.objects.filter(Date__range=(from_date, to_date), branch=branch)

            except ValueError:
                print("Invalid date format.")  # Handle invalid date formats
        else:
            print("Both from_date and to_date are required.")
    return render(request, 'adminViewExpenses.html', {'expenses': expenses})

def branchConsignorView(request):
    uid = request.session.get('username')
    if uid:
        branch = Branch.objects.get(email=uid)
        branchname = branch.companyname
        consignor=Consignor.objects.filter(branch=branchname)
    return render(request,'branchConsignorView.html',{'consignor':consignor})

def branchConsigneeView(request):
    uid = request.session.get('username')
    if uid:
        branch = Branch.objects.get(email=uid)
        branchname = branch.companyname
        consignee = Consignee.objects.filter(branch=branchname)
    return render(request,'branchConsigneeView.html',{'consignee':consignee})

def adminConsignorView(request):
    consignor = []  # Initialize consignee as an empty list

    if request.method == 'POST':
        branch = request.POST.get('t2')
        print(f"Branch: {branch}")  # Debugging: Print the branch name
        consignor = Consignor.objects.filter(branch=branch)
        print(f"Consignee: {consignor}")  # Debugging: Print the consignee queryset

    return render(request,'adminConsignorView.html',{'consignor':consignor})


def adminConsigneeView(request):
    consignee = []  # Initialize consignee as an empty list

    if request.method == 'POST':
        branch = request.POST.get('t2')
        print(f"Branch: {branch}")  # Debugging: Print the branch name
        consignee = Consignee.objects.filter(branch=branch)
        print(f"Consignee: {consignee}")  # Debugging: Print the consignee queryset

    return render(request, 'adminConsigneeView.html', {'consignee': consignee})

def adminstaff_view(request):
    branch = request.POST.get('branch', '')
    if branch:
        # Filter staff data based on the branch name (case-insensitive search)
        staff_data = Staff.objects.filter(Branch__icontains=branch)
    else:
        # If no branch is provided, fetch all staff data
        staff_data = Staff.objects.all()

    # Render the template with the filtered data
    return render(request, 'adminstaff_view.html', {'data': staff_data, 'branch': branch})


from django.utils.dateparse import parse_date


from django.utils.dateparse import parse_date


def adminView_Consignment(request):
    consignments_list = []

    if request.method == 'POST':
        branch = request.POST.get('t2')
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')
        order = request.POST.get('orderno')

        # Parse dates
        from_date = parse_date(from_date_str) if from_date_str else None
        to_date = parse_date(to_date_str) if to_date_str else None

        print(f"Branch: {branch}")  # Debugging: Print the branch name
        print(f"Order: {order}")  # Debugging: Print the branch name
        print(f"From Date: {from_date}")  # Debugging: Print the from date
        print(f"To Date: {to_date}")  # Debugging: Print the to date

        # Start building the query
        queryset = AddConsignment.objects.all()

        if branch:
            queryset = queryset.filter(branch=branch)
        if order:
            queryset = queryset.filter(track_id=order)
        if from_date and to_date:
            queryset = queryset.filter(date__range=(from_date, to_date))
        elif from_date:
            queryset = queryset.filter(date__gte=from_date)
        elif to_date:
            queryset = queryset.filter(date__lte=to_date)

        print(f"Filtered Consignments: {queryset}")  # Debugging: Print the filtered queryset

        # Collect details from the filtered queryset
        for consignment in queryset:
            details = {
                'date': consignment.date,
                'track_id': consignment.track_id,
                'barcode_number': consignment.barcode_number,
                'branch': consignment.branch,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'sender_name': consignment.sender_name,
                'sender_mobile': consignment.sender_mobile,
                'sender_address': consignment.sender_address,
                'receiver_name': consignment.receiver_name,
                'receiver_mobile': consignment.receiver_mobile,
                'receiver_address': consignment.receiver_address,
                'total_cost': consignment.total_cost,
                'pieces': consignment.pieces,
                'weight': consignment.weight,
                'pay_status': consignment.pay_status,
                'remark': consignment.remark,
                'eway_bill': consignment.eway_bill,
                'status': consignment.status,
                'category': consignment.category,  # Store product details directly
            }
            consignments_list.append(details)

    return render(request, 'adminView_Consignment.html', {'consignments_list': consignments_list})

def admininvoiceConsignment(request, track_id):
    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)

        # Check if any consignments are returned
        if not consignments.exists():
            raise ObjectDoesNotExist("No consignments found.")

        # Get branch details from the first consignment
        branch = consignments.first().branch  # Ensure branch is retrieved from the first consignment
        branchdetails = Branch.objects.get(companyname=branch)

        # Create a list to hold details of each consignment
        consignment_details = []
        copy_types = set()

        for consignment in consignments:
            # Ensure that 'barcode_image' is explicitly added here
            details = {
                'track_id': consignment.track_id,
                'sender_name': consignment.sender_name,
                'receiver_name': consignment.receiver_name,
                'sender_mobile': consignment.sender_mobile,
                'receiver_mobile': consignment.receiver_mobile,
                'sender_address': consignment.sender_address,
                'receiver_address': consignment.receiver_address,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'freight': consignment.freight,
                'hamali': consignment.hamali,
                'door_charge': consignment.door_charge,
                'total_cost': consignment.total_cost,
                'pay_status': consignment.pay_status,
                'pieces': consignment.pieces,
                'category': consignment.category,
                'weight': consignment.weight,
                'eway_bill': consignment.eway_bill,
                'date': consignment.date,
                'barcode_image': consignment.barcode_image  # Handle the image URL
            }
            consignment_details.append(details)

            # Collect unique copy types
            copy_types.add(consignment.copy_type)

        # Convert copy types set to a list
        copy_types_list = list(copy_types)

    except ObjectDoesNotExist:
        consignment_details = []
        copy_types_list = []
        branchdetails = None  # Handle branch details if no consignment found

    return render(request, 'admininvoiceConsignment.html', {
        'consignment_details': consignment_details,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types_list)
    })


def staffinvoiceConsignment(request, track_id):
    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)
        uid = request.session.get('username')
        data = Staff.objects.get(staffPhone=uid)
        name = data.Branch
        branchdetails = Branch.objects.get(companyname=name)

        # Create a list to hold details of each consignment
        consignment_details = []
        copy_types = set()

        for consignment in consignments:
            # Ensure that 'barcode_image' is explicitly added here
            details = {
                'track_id': consignment.track_id,
                'sender_name': consignment.sender_name,
                'receiver_name': consignment.receiver_name,
                'sender_mobile': consignment.sender_mobile,
                'receiver_mobile': consignment.receiver_mobile,
                'sender_address': consignment.sender_address,
                'receiver_address': consignment.receiver_address,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'freight': consignment.freight,
                'hamali': consignment.hamali,
                'door_charge': consignment.door_charge,
                'total_cost': consignment.total_cost,
                'pay_status': consignment.pay_status,
                'pieces': consignment.pieces,
                'category': consignment.category,
                'weight': consignment.weight,
                'eway_bill': consignment.eway_bill,
                'date': consignment.date,
                'barcode_image': consignment.barcode_image  # Handle the image URL
            }
            consignment_details.append(details)

            # Collect unique copy types
            copy_types.add(consignment.copy_type)

        # Convert copy types set to a list
        copy_types_list = list(copy_types)

    except ObjectDoesNotExist:
        consignment_details = []
        copy_types_list = []
        branchdetails = None  # Handle branch details if no consignment found

    return render(request, 'staffinvoiceConsignment.html', {
        'consignment_details': consignment_details,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types_list)
    })




def cash_collection(request):
    # Initialize filters
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    paid = request.GET.getlist('payment')  # Allow multiple payment modes
    branch = request.GET.get('branch')

    # Start building the query
    queryset = AddConsignment.objects.all()

    # Apply payment filter if provided
    if paid:
        queryset = queryset.filter(pay_status__in=paid)  # Use `__in` to filter multiple values

    # Apply date range filter if both from_date and to_date are provided
    if from_date_str and to_date_str:
        try:
            # Convert the date strings to datetime objects
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

            # Ensure that the range includes both dates
            queryset = queryset.filter(date__range=(from_date, to_date))

        except ValueError:
            # Handle invalid date input
            return render(request, 'cash_collection.html', {
                'accounts': [],
                'total_rows': 0,
                'total_amount': 0,
                'error': 'Invalid date format.'
            })

    # Apply branch filter if provided
    if branch:
        queryset = queryset.filter(branch__icontains=branch)

    # Convert queryset to a list for further processing
    queryset_list = list(queryset)

    # Group by track_id and keep only the first record in each group
    grouped_userdata = {}
    for consignment in queryset_list:
        if consignment.track_id not in grouped_userdata:
            grouped_userdata[consignment.track_id] = consignment

    # Convert the grouped dictionary to a list
    grouped_queryset = list(grouped_userdata.values())

    # Calculate total rows and total amount
    total_rows = len(grouped_queryset)
    total_amount = sum(consignment.total_cost for consignment in grouped_queryset)

    context = {
        'accounts': grouped_queryset,
        'total_rows': total_rows,
        'total_amount': total_amount,
    }

    # If no data is found after filtering, return with no records found
    if not grouped_queryset:
        return render(request, 'cash_collection.html', {'accounts': [], 'total_rows': 0, 'total_amount': 0})

    return render(request, 'cash_collection.html', context)


def category(request):
    categories = Category.objects.all()

    # Handle form submission for creating a new category
    if request.method == "POST":
        if 'create_category' in request.POST:  # Create category form
            new_cat_name = request.POST.get('new_cat_name')
            prefix = request.POST.get('prefix')
            freight = request.POST.get('freight')

            if new_cat_name:
                Category.objects.create(
                    cat_name=new_cat_name,
                    prefix=prefix,
                   freight=freight
                )
            return redirect('category')

    return render(request, 'category.html', {'categories': categories})

def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        new_cat_name = request.POST.get('cat_name')
        prefix = request.POST.get('prefix')
        freight = request.POST.get('freight')

        if new_cat_name:
            category.cat_name = new_cat_name
            category.prefix = prefix
            category.freight = freight
            category.save()
            return redirect('category')

    return render(request, 'edit_category.html', {'category': category})

def location(request):
    location = Location.objects.all()

    # Handle form submission for creating a new category
    if request.method == "POST":
        if 'create_location' in request.POST:  # Create category form
            location = request.POST.get('location')


            if location:
                Location.objects.create(
                    location=location,
                )
            return redirect('location')

    return render(request, 'location.html', {'locations': location})


def edit_location(request, location_id):
    locations= get_object_or_404(Location, id=location_id)

    if request.method == "POST":
        location = request.POST.get('location')


        if location:
            locations.location = location
            locations.save()
            return redirect('location')

    return render(request, 'edit_location.html', {'location': locations})

def get_category_details(request):
    cat_name = request.GET.get('cat_name', None)

    if cat_name:
        try:
            category = Category.objects.get(prefix=cat_name)
            data = {
                'freight': category.freight,  # Assuming your model has a 'freight' field
            }
            return JsonResponse(data)
        except Category.DoesNotExist:
            return JsonResponse({'error': 'Category not found'}, status=404)

    return JsonResponse({'error': 'No category selected'}, status=400)


def dashboard(request):
    consignments_summary = None  # Default value if no query is made
    from_date = None
    to_date = None

    if request.method == 'POST':
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')

        # Parse the date strings to proper date objects
        from_date = parse_date(from_date)
        to_date = parse_date(to_date)

        if from_date and to_date:
            # Filter the AddConsignment table by date range and group by category
            consignments_summary = (
                AddConsignment.objects.filter(date__range=[from_date, to_date],status='Active')
                .values('category')  # Group by the category field in the AddConsignment table
                .annotate(
                    total_weight=Sum('weight'),  # Total weight per category
                    count_track_id=Count('track_id'),  # Count of track_id per category
                    total_pieces=Sum('pieces'),  # Count of track_id per category
                    grand_total=Sum('total_cost'),  # Grand total (if you have a total_cost field)
                )
            )

    return render(request, 'dashboard.html', {
        'consignments_summary': consignments_summary,
        'from_date': from_date,
        'to_date': to_date
    })



def partywise_list(request):
    # Get filter values from the request
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    sender_name = request.GET.get('sender_name')

    # Start building the query
    queryset = AddConsignment.objects.all()

    # Apply date range filter if both from_date and to_date are provided
    if from_date_str and to_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

            # Filter the queryset by the date range
            queryset = queryset.filter(date__range=(from_date, to_date))
        except ValueError:
            return render(request, 'partywise_report.html', {
                'error': 'Invalid date format.'
            })

    # Apply sender_name filter if provided
    if sender_name:
        queryset = queryset.filter(sender_name__icontains=sender_name)

    # Group by sender_name and calculate sum of pieces, total cost, and count of track_id
    consignments_by_sender = queryset.values('sender_name').annotate(
        total_pieces=Sum('pieces'),
        total_cost=Sum('total_cost'),
        track_id_count=Count('track_id', distinct=True)
    ).order_by('sender_name')

    # Pass the aggregated data to the template
    context = {
        'consignments_by_sender': consignments_by_sender,
        'from_date': from_date_str,
        'to_date': to_date_str,
        'sender_name': sender_name,    }

    return render(request, 'partywise_report.html', context)


def partywise_detail(request, sender_name):
    # Get filter values from the request
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    # Start building the query
    consignments = AddConsignment.objects.filter(sender_name=sender_name)

    # Apply date range filter if both from_date and to_date are provided
    if from_date_str and to_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

            # Filter the queryset by the date range
            consignments = consignments.filter(date__range=(from_date, to_date))
        except ValueError:
            return render(request, 'partywise_detail.html', {
                'error': 'Invalid date format.',
                'sender_name': sender_name,
            })

    if not consignments.exists():
        return render(request, 'partywise_detail.html', {'error': 'No consignments found for this sender.'})

    # Aggregate details based on Consignment_id
    aggregated_data = consignments.values(
        'Consignment_id',
        'track_id',
        'sender_name',
        'sender_mobile',
        'sender_address',
        'receiver_name',
        'receiver_mobile',
        'receiver_address',
        'date',
        'route_from',
        'route_to',
        'prod_price',
        'branch',
        'name',
        'time',
        'copy_type',
        'delivery',
        'eway_bill'
    ).annotate(
        total_cost=Sum('total_cost'),
        pieces=Sum('pieces'),
        weight=Sum('weight'),
        freight=Sum('freight'),
        hamali=Sum('hamali'),
        door_charge=Sum('door_charge'),
        st_charge=Sum('st_charge'),
    ).order_by('Consignment_id')

    # Create a list of dictionaries for the final data to be displayed
    detailed_data = []
    for consignment in aggregated_data:
        descriptions = consignments.filter(Consignment_id=consignment['Consignment_id']).values_list('desc_product', flat=True)
        # Append each description with aggregated data
        detailed_data.append({
            **consignment,
            'desc_products': descriptions
        })

    # Calculate total pieces for the sender
    total_pieces = consignments.aggregate(total_pieces=Sum('pieces'))['total_pieces'] or 0

    return render(request, 'partywise_detail.html', {
        'sender_name': sender_name,
        'consignments': detailed_data,
        'total_pieces': total_pieces
    })



def account_report(request):
    # Get filter values from the request
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    branch = request.GET.get('branch')
    sender_name = request.GET.get('sender_name')

    # Start building the query
    queryset = Account.objects.all()

    # Apply date range filter if both from_date and to_date are provided
    if from_date_str and to_date_str:
        try:
            # Convert the date strings to datetime objects
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

            # Ensure that the range includes both dates
            queryset = queryset.filter(Date__range=(from_date, to_date))
        except ValueError:
            # Handle invalid date input
            return render(request, 'account_report.html', {
                'accounts': [],
                'error': 'Invalid date format.'
            })

    # Apply branch filter if provided
    if branch:
        queryset = queryset.filter(Branch__icontains=branch)

    # Apply sender_name filter if provided
    if sender_name:
        queryset = queryset.filter(sender_name__icontains=sender_name)

    # Get the filtered results
    accounts = queryset

    # If no data found, add a message
    if not accounts.exists():
        return render(request, 'account_report.html', {
            'accounts': [],
            'message': 'No records found for the given filters.'
        })

    # Return the filtered data to the template
    context = {
        'accounts': accounts,
        'from_date': from_date_str,
        'to_date': to_date_str,
        'branch': branch,
        'sender_name': sender_name,
    }
    return render(request, 'account_report.html', context)


def get_account_details(request):
    branch = request.GET.get('branch', '')
    if branch:
        accounts = Account.objects.filter(Branch__icontains=branch)
        accounts_data = list(accounts.values('Date','track_number', 'sender_name', 'Branch', 'headname', 'TrType', 'debit', 'credit', 'Balance'))
        return JsonResponse(accounts_data, safe=False)
    return JsonResponse([], safe=False)

def unloaded_LR_report(request):
    # Extract query parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Initialize variables for start_date and end_date
    start_date = None
    end_date = None

    # Convert string dates to datetime objects
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            pass  # Handle invalid date format if necessary

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            pass  # Handle invalid date format if necessary

    # If end_date is provided, extend it to the end of the day
    if end_date:
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Filter consignments based on date range
    consignments = AddConsignmentTemp.objects.all()

    if start_date:
        consignments = consignments.filter(date__gte=start_date)

    if end_date:
        consignments = consignments.filter(date__lte=end_date)

    # Render the template with the filtered consignments
    return render(request, 'unloaded_LR_report.html', {'consignments': consignments})

def advance_report(request):
    driver_name = request.GET.get('driver_name')
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    # Convert date strings to date objects
    from_date = datetime.strptime(from_date_str, '%Y-%m-%d') if from_date_str else None
    to_date = datetime.strptime(to_date_str, '%Y-%m-%d') if to_date_str else None

    # Initialize the filters dictionary
    filters = {}
    if driver_name:
        filters['DriverName'] = driver_name
    if from_date and to_date:
        filters['Date__range'] = [from_date, to_date]

    # Add the condition for AdvGiven to be more than 0
    filters['AdvGiven__gt'] = 0

    # Fetch the results based on the filters
    results = TripSheetPrem.objects.filter(**filters)

    return render(request, 'advance_report.html', {
        'results': results,
        'driver_name': driver_name,
        'from_date': from_date_str,
        'to_date': to_date_str
    })



def profit_report(request):
    # Get the from_date and to_date from the request (if provided)
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    from_date = parse_date(from_date_str) if from_date_str else None
    to_date = parse_date(to_date_str) if to_date_str else None

    # Query all consignments and expenses
    consignments = AddConsignment.objects.all()
    expenses = Expenses.objects.all()

    # Filter by date range if provided
    if from_date and to_date:
        consignments = consignments.filter(date__range=[from_date, to_date])
        expenses = expenses.filter(Date__range=[from_date, to_date])

    # Track already processed track_ids
    processed_track_ids = set()

    # This list will store the unique consignments
    unique_consignments = []

    # Iterate over all consignments to ensure only unique track_id costs are added
    for consignment in consignments:
        track_id = consignment.track_id
        # If track_id is not already processed, add its total_cost to the unique list
        if track_id not in processed_track_ids:
            processed_track_ids.add(track_id)
            unique_consignments.append(consignment)

    # Now group by date and branch, summing the total_cost of the unique consignments
    consignments_grouped = (
        AddConsignment.objects.filter(id__in=[c.id for c in unique_consignments])
        .values('date', 'branch')
        .annotate(total_cost=Sum('total_cost'))
        .order_by('date', 'branch')
    )

    # Group expenses by date and branch, and calculate total Amount for each group
    expenses_grouped = expenses.values('Date', 'branch').annotate(
        total_amount=Sum('Amount')
    ).order_by('Date', 'branch')

    # Calculate grand totals for consignments and expenses
    grand_total_consignment = sum(item['total_cost'] for item in consignments_grouped)
    grand_total_expenses = sum(item['total_amount'] for item in expenses_grouped)

    # Calculate combined grand total
    combined_grand_total = grand_total_consignment + grand_total_expenses

    # Calculate profit or loss
    total_balance = grand_total_consignment - grand_total_expenses

    # Set profit and loss
    profit = total_balance if total_balance > 0 else 0
    loss = abs(total_balance) if total_balance < 0 else 0

    # Pass the grouped data and totals to the template
    return render(request, 'profit_report.html', {
        'consignments': consignments_grouped,
        'expenses': expenses_grouped,
        'grand_total_consignment': grand_total_consignment,
        'grand_total_expenses': grand_total_expenses,
        'combined_grand_total': combined_grand_total,
        'profit': profit,
        'loss': loss,
        'from_date': from_date_str,
        'to_date': to_date_str,
    })



def consignorEdit(request, id):
    # Fetch the consignor data
    data = Consignor.objects.filter(id=id).first()

    if request.method == "POST":
        # Get POST data
        post_data = request.POST

        # Update Consignor fields
        data.sender_name = post_data.get('a1')
        data.sender_mobile = post_data.get('a2')
        data.receiver_name = post_data.get('a3')
        data.sender_address = post_data.get('a4')
        data.sender_password = post_data.get('a5')

        # Save Consignor data
        data.save()

        # Check if sender_mobile exists in the Login table
        sender_mobile = post_data.get('a2')
        sender_name = post_data.get('a1')
        new_password = post_data.get('a5')
        login_user = Login.objects.filter(username=sender_mobile).first()

        if login_user:
            # Update the existing login entry
            login_user.username = sender_mobile
            if new_password:  # Update password only if a new one is provided
                login_user.password = new_password  # Plaintext password (not recommended)
            login_user.save()
        else:
            # Create a new login entry if sender_mobile doesn't exist
            Login.objects.create(
                username=sender_mobile,
                password=new_password,  # Plaintext password (not recommended)
                utype='customer', # Set the user type as 'customer'
                name=sender_name
            )

        # Redirect after successful update
        return redirect(adminConsignorView)

    return render(request, 'consignorEdit.html', {'data': data})


def consigneeEdit(request,id):
    data=Consignee.objects.filter(id=id).first()
    if request.method == "POST":
        # Get POST data
        post_data = request.POST

        data.receiver_name = post_data.get('a5')
        data.receiver_mobile = post_data.get('a6')
        data.receiver_GST = post_data.get('a7')
        data.receiver_address = post_data.get('a8')
        data.receiver_password = post_data.get('a9')

        # Save userdata
        data.save()
        # Check if sender_mobile exists in the Login table
        receiver_mobile = post_data.get('a6')
        receiver_name = post_data.get('a5')
        new_password = post_data.get('a9')
        login_user = Login.objects.filter(username=receiver_mobile).first()

        if login_user:
            # Update the existing login entry
            login_user.username = receiver_mobile
            if new_password:  # Update password only if a new one is provided
                login_user.password = new_password  # Plaintext password (not recommended)
            login_user.save()
        else:
            # Create a new login entry if sender_mobile doesn't exist
            Login.objects.create(
                username=receiver_mobile,
                password=new_password,  # Plaintext password (not recommended)
                utype='customer',  # Set the user type as 'customer'
                name=receiver_name
            )
        return redirect(adminConsigneeView)
    return render(request,'consigneeEdit.html',{'data':data})

def customerConsignment(request):
    if request.method == "POST":
        try:
            now = datetime.now()
            con_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")

            uid = request.session.get('username')
            branch = Login.objects.get(username=uid)
            username = branch.name

            # Get the last track_id and increment it
            last_track_id = AddConsignment.objects.aggregate(Max('track_id'))['track_id__max']
            track_id = int(last_track_id) + 1 if last_track_id else 1001
            con_id = str(track_id)

            # Get the last Consignment_id and increment it
            last_con_id = AddConsignment.objects.aggregate(Max('Consignment_id'))['Consignment_id__max']
            Consignment_id = last_con_id + 1 if last_con_id else 1001
            Consignment_id = str(Consignment_id)

            # Sender and Receiver details
            send_name = request.POST.get('a1')
            send_mobile = request.POST.get('a2')
            send_address = request.POST.get('a4')
            sender_GST = request.POST.get('sendergst')
            rec_name = request.POST.get('a5')
            rec_mobile = request.POST.get('a6')
            rec_address = request.POST.get('a8')
            rec_GST = request.POST.get('receivergst')
            route_from = request.POST.get('from')
            route_to = request.POST.get('to')
            branch_value = request.POST.get('branch')

            # Validation for required fields
            if not send_name or not rec_name:
                error_message = 'Sender and Receiver names are required.'
                logger.error(error_message)  # Log error details
                return JsonResponse({'error': error_message}, status=400)

            # Check if route_to matches any location in Location model
            location_match = Location.objects.filter(location=route_to).exists()
            if not location_match:
                invalid_locations = Location.objects.values_list('location', flat=True)
                error_message = f'The destination route does not match the allowed locations: {", ".join(invalid_locations)}.'
                logger.warning(error_message)  # Log warning for invalid locations
                return JsonResponse({'error': error_message}, status=400)

            # Copies (consignor, consignee, etc.)
            copies = []
            if request.POST.get('consignor_copy'):
                copies.append('Consignor Copy')
            if request.POST.get('consignee_copy'):
                copies.append('Consignee Copy')
            if request.POST.get('lorry_copy'):
                copies.append('Lorry Copy')
            copy_type = ', '.join(copies)

            # Create or update Consignor
            try:
                consignor, _ = Consignor.objects.update_or_create(
                    sender_name=send_name,
                    defaults={
                        'sender_mobile': send_mobile,
                        'sender_address': send_address,
                        'sender_GST': sender_GST,
                        'branch': branch_value,
                        'username':username
                    }
                )
            except (IntegrityError, ValidationError) as e:
                logger.exception("Error saving consignor")  # Log the complete traceback
                return JsonResponse({'error': 'Error saving consignor. Please check your inputs.'}, status=400)

            # Create or update Consignee
            try:
                consignee, _ = Consignee.objects.update_or_create(
                    receiver_name=rec_name,
                    defaults={
                        'receiver_mobile': rec_mobile,
                        'receiver_address': rec_address,
                        'receiver_GST': rec_GST,
                        'branch': branch_value,
                        'username': username
                    }
                )
            except (IntegrityError, ValidationError) as e:
                logger.exception("Error saving consignee")  # Log the complete traceback
                return JsonResponse({'error': 'Error saving consignee. Please check your inputs.'}, status=400)

            # Other consignment details
            remark = request.POST.get('remark')
            delivery = request.POST.get('delivery_option')
            pieces = request.POST.get('packages')
            prod_price = request.POST.get('prod_price')
            eway_bill = request.POST.get('ewaybill_no')
            weight = request.POST.get('weight')
            category = request.POST.get('category')
            freight = float(request.POST.get('freight', 0))
            hamali = request.POST.get('hamali', 0)
            door_charge = request.POST.get('door_charge', 0)
            cgst = request.POST.get('cgst', 0)
            sgst = request.POST.get('sgst', 0)
            gst = request.POST.get('gst', 0)
            cost = float(request.POST.get('cost', 0))
            pay_status = request.POST.get('payment')

            unique_id = str(uuid.uuid4().int)[:12]


            # Determine the appropriate name based on pay_status
            account_name = send_name if pay_status == 'Shipper A/C' else rec_name if pay_status == 'Receiver A/C' else send_name

            # Save to AddConsignment
            try:
                consignment = AddConsignment.objects.create(
                    track_id=con_id,
                    Consignment_id=Consignment_id,
                    sender_name=send_name,
                    sender_mobile=send_mobile,
                    sender_address=send_address,
                    sender_GST=sender_GST,
                    receiver_name=rec_name,
                    receiver_mobile=rec_mobile,
                    receiver_address=rec_address,
                    receiver_GST=rec_GST,
                    pieces=pieces,
                    prod_price=prod_price,
                    category=category,
                    weight=weight,
                    freight=freight,
                    hamali=hamali,
                    door_charge=door_charge,
                    gst=gst,
                    cgst=cgst,
                    sgst=sgst,
                    route_from=route_from,
                    route_to=route_to,
                    total_cost=cost,
                    date=con_date,
                    pay_status=pay_status,
                    branch=branch_value,
                    name=username,
                    time=current_time,
                    copy_type=copy_type,
                    delivery=delivery,
                    eway_bill=eway_bill,
                    barcode_number=unique_id,
                    remark=remark,
                    status='Active',
                    reason='Consignment Added'
                )
                consignmenttemp = AddConsignmentTemp.objects.create(
                    track_id=con_id,
                    Consignment_id=Consignment_id,
                    sender_name=send_name,
                    sender_mobile=send_mobile,
                    sender_address=send_address,
                    sender_GST=sender_GST,
                    receiver_name=rec_name,
                    receiver_mobile=rec_mobile,
                    receiver_address=rec_address,
                    receiver_GST=rec_GST,
                    pieces=pieces,
                    prod_price=prod_price,
                    category=category,
                    weight=weight,
                    freight=freight,
                    hamali=hamali,
                    door_charge=door_charge,
                    gst=gst,
                    cgst=cgst,
                    sgst=sgst,
                    route_from=route_from,
                    route_to=route_to,
                    total_cost=cost,
                    date=con_date,
                    pay_status=pay_status,
                    branch=branch_value,
                    name=username,
                    time=current_time,
                    copy_type=copy_type,
                    delivery=delivery,
                    eway_bill=eway_bill,
                    barcode_number=unique_id,
                    remark=remark,
                    status='Active',
                    reason='Consignment Added'
                )
            except (IntegrityError, ValidationError) as e:
                logger.exception("Error saving consignment")  # Log the complete traceback
                return JsonResponse({'error': 'Error saving consignment. Please check your inputs.'}, status=400)

            # Barcode generation and saving
            barcode_number = str(track_id)
            code128 = Code128(barcode_number, writer=ImageWriter())
            barcode_path = os.path.join(settings.MEDIA_ROOT, 'barcode', f'{track_id}.png')

            try:
                with open(barcode_path, 'wb') as barcode_file:
                    code128.write(barcode_file)

                consignment.barcode_image.save(f'barcode/{track_id}.png', File(open(barcode_path, 'rb')))
                consignment.barcode_number = barcode_number
                consignment.save()
            except Exception as e:
                logger.exception("Error generating barcode")  # Log the complete traceback
                return JsonResponse({'error': 'Error generating barcode. Please try again later.'}, status=400)

            # Account processing
            try:
                previous_balance_entry = Account.objects.filter(sender_name=send_name).order_by('-Date').first()
                previous_balance = float(previous_balance_entry.Balance) if previous_balance_entry else 0.0
                updated_balance = previous_balance + cost

                account_entry, created = Account.objects.update_or_create(
                    track_number=con_id,
                    defaults={
                        'Date': now,
                        'debit': cost,
                        'credit': 0,
                        'TrType': "sal",
                        'particulars': f"{con_id} Debited",
                        'Balance': updated_balance,
                        'sender_name': account_name,
                        'headname': username,
                        'Branch': branch_value
                    }
                )
            except (IntegrityError, ValidationError) as e:
                logger.exception("Error updating account")  # Log the complete traceback
                return JsonResponse({'error': 'Error updating account. Please check your inputs.'}, status=400)

            # After saving the consignment
            return JsonResponse({
                'message': 'Consignment added successfully!',
                'track_id': con_id  # Include the track_id in the response
            }, status=200)

        except Exception as e:
            logger.exception("An unexpected error occurred")  # Log the complete traceback
            return JsonResponse({'error': 'An unexpected error occurred. Please try again later.'}, status=500)

    else:
        # Fetch categories
        cat = Category.objects.all()
        branchname = Branch.objects.all()
        return render(request, 'customerConsignment.html', {'cat': cat,'branchname':branchname})

def get_consignee_name_customer(request):
    query = request.GET.get('query', '')
    uid = request.session.get('username')
    branch = Login.objects.get(username=uid)
    username = branch.name
    if query:
        receiver_names = Consignee.objects.filter(receiver_name__icontains=query,username=username).values_list('receiver_name', flat=True)
        print('sender_names numbers:', list(receiver_names))  # Debugging: check the data in the terminal
        return JsonResponse(list(receiver_names), safe=False)
    return JsonResponse([], safe=False)

def get_rec_details_customer(request):
    name = request.GET.get('name', '')
    uid = request.session.get('username')
    branch = Login.objects.get(username=uid)
    username = branch.name
    data = {}

    if name:
        try:
            consignee = Consignee.objects.get(receiver_name=name,username=username)  # Use .get() if you expect a single result
            data = {
                'receiver_mobile': consignee.receiver_mobile,
                'receiver_GST': consignee.receiver_GST,
                'receiver_address': consignee.receiver_address,
            }
        except Consignee.DoesNotExist:
            data = {'error': 'Consignee not found'}

    return JsonResponse(data)

def get_consignee_number_customer(request):
    query = request.GET.get('query', '')
    uid = request.session.get('username')
    branch = Login.objects.get(username=uid)
    username = branch.name
    if query:
        receiver_mobiles = Consignee.objects.filter(receiver_mobile__icontains=query,username=username).values_list('receiver_mobile', flat=True)
        print('receiver_mobile numbers:', list(receiver_mobiles))  # Debugging: check the data in the terminal
        return JsonResponse(list(receiver_mobiles), safe=False)
    return JsonResponse([], safe=False)

def get_receiver_number_details_customer(request):
    name = request.GET.get('name', '')
    uid = request.session.get('username')
    branch = Login.objects.get(username=uid)
    username = branch.name
    if name:
        consignee = Consignee.objects.filter(receiver_mobile=name,username=username).first()
        if consignee:
            data = {
                'receiver_name': consignee.receiver_name,
                'receiver_GST': consignee.receiver_GST,
                'receiver_address': consignee.receiver_address,
            }
        else:
            data = {}
    else:
        data = {}

    return JsonResponse(data)

def get_consignor_number_customer(request):
    query = request.GET.get('query', '')
    uid = request.session.get('username')
    branch = Login.objects.get(username=uid)
    username = branch.name
    if query:
        sender_mobiles = Consignor.objects.filter(sender_mobile__icontains=query,username=username).values_list('sender_mobile', flat=True)
        print('sender_mobiles numbers:', list(sender_mobiles))  # Debugging: check the data in the terminal
        return JsonResponse(list(sender_mobiles), safe=False)
    return JsonResponse([], safe=False)

def get_sender_number_details_customer(request):
    name = request.GET.get('name', '')
    uid = request.session.get('username')
    branch = Login.objects.get(username=uid)
    username = branch.name
    if name:
        consignor = Consignor.objects.filter(sender_mobile=name,username=username).first()
        if consignor:
            data = {
                'sender_name': consignor.sender_name,
                'sender_GST': consignor.sender_GST,
                'sender_address': consignor.sender_address,
            }
        else:
            data = {}
    else:
        data = {}

    return JsonResponse(data)

def get_consignor_name_customer(request):
    query = request.GET.get('query', '')
    uid = request.session.get('username')
    branch = Login.objects.get(username=uid)
    username = branch.name
    if query:
        sender_names = Consignor.objects.filter(sender_name__icontains=query,username=username).values_list('sender_name', flat=True)
        print('sender_names numbers:', list(sender_names))  # Debugging: check the data in the terminal
        return JsonResponse(list(sender_names), safe=False)
    return JsonResponse([], safe=False)

def get_sender_details_customer(request):
    name = request.GET.get('name', '')
    uid = request.session.get('username')
    branch = Login.objects.get(username=uid)
    username = branch.name
    if name:
        consignor = Consignor.objects.filter(sender_name=name,username=username).first()
        if consignor:
            data = {
                'sender_mobile': consignor.sender_mobile,
                'sender_GST': consignor.sender_GST,
                'sender_address': consignor.sender_address,
            }
        else:
            data = {}
    else:
        data = {}

    return JsonResponse(data)


def stages(request):
    delivered_lrnos = Stages.objects.filter(stage='Delivered').values_list('LrNo', flat=True)
    consignments = AddConsignment.objects.exclude(track_id__in=delivered_lrnos)

    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')
        print("Incoming POST data:", request.POST)  # Print all POST data

        # Get order input
        order1 = request.POST.get('orderno', '').strip()
        print(f"Order input received: '{order1}'")

        # Clean and split barcodes
        barcodes = [barcode.strip() for barcode in order1.split(',') if barcode.strip()]
        if not barcodes:
            print("No barcodes provided.")
            return render(request, 'stages.html', {'consignments': consignments, 'error': 'No barcodes provided.'})

        print(f"Barcodes processed: {barcodes}")

        # Parse dates
        from_date = parse_date(from_date_str) if from_date_str else None
        to_date = parse_date(to_date_str) if to_date_str else None

        if barcodes:
            consignments = consignments.filter(barcode_number__in=barcodes)
            print(f"Consignments after barcode filter: {consignments.count()}")

        if from_date and to_date:
            consignments = consignments.filter(date__range=(from_date, to_date))
        elif from_date:
            consignments = consignments.filter(date__gte=from_date)
        elif to_date:
            consignments = consignments.filter(date__lte=to_date)

        print(f"Consignments fetched: {consignments.count()}")

        now = timezone.now()
        con_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")  # Format time without milliseconds
        time_without_microseconds = datetime.strptime(current_time, "%H:%M:%S").time()

        uid = request.session.get('username')
        branchdetails = Branch.objects.get(email=uid)
        branchname = branchdetails.companyname
        username = branchdetails.headname
        address = branchdetails.address

        lrno = request.POST.get('lrno')
        picked = request.POST.get('picked')
        sd = request.POST.get('sd')
        transit = request.POST.get('transit')
        dd = request.POST.get('dd')
        out = request.POST.get('out')
        delivered = request.POST.get('delivered')

        # Determine which stage to save
        stage = None
        if picked:
            stage = picked
        elif sd:
            stage = sd
        elif transit:
            stage = transit
        elif dd:
            stage = dd
        elif out:
            stage = out
        elif delivered:
            stage = delivered

        selected_ids = request.POST.getlist('selected_ids')  # Get selected track_ids

        if stage and selected_ids:  # Only create an entry if a stage is set and consignments are selected
            for track_id in selected_ids:
                try:
                    # Save each selected consignment stage
                    Stages.objects.create(
                        Date=con_date,
                        Time=time_without_microseconds,  # Store as a time object without microseconds
                        LrNo=track_id,
                        username=username,
                        Branch=branchname,
                        branchlocation=address,
                        stage=stage,
                    )
                except Exception as e:
                    print(f"Error saving stage for track_id {track_id}: {e}")

    return render(request, 'stages.html', {'consignments': consignments})



def save_stage(request):
    if request.method == 'POST':
        # Retrieve session user information
        uid = request.session.get('username')
        try:
            branchdetails = Branch.objects.get(email=uid)
        except Branch.DoesNotExist:
            return render(request, 'error.html', {'message': 'Branch details not found!'})

        branchname = branchdetails.companyname
        username = branchdetails.headname
        address = branchdetails.address

        # Capture stage information from checkboxes
        picked = request.POST.get('picked')
        sd = request.POST.get('sd')
        transit = request.POST.get('transit')
        dd = request.POST.get('dd')
        out = request.POST.get('out')
        delivered = request.POST.get('delivered')

        # Determine the stage to save based on the checked box
        stage = None
        if picked:
            stage = picked
        elif sd:
            stage = sd
        elif transit:
            stage = transit
        elif dd:
            stage = dd
        elif out:
            stage = out
        elif delivered:
            stage = delivered

        # Get selected consignment IDs from checkboxes
        selected_ids = request.POST.getlist('selected_ids')

        if stage and selected_ids:
            con_date = timezone.now().date()
            time_without_microseconds = timezone.now().time().replace(microsecond=0)

            # Track if any new stages were saved
            any_new_stages_saved = False

            # Loop through selected consignment IDs to save each consignment's stage
            for track_id in selected_ids:
                # Check if the stage already exists for this LrNo
                existing_stage = Stages.objects.filter(LrNo=track_id, stage=stage).first()
                if existing_stage:
                    # Notify the user about the duplicate stage
                    messages.warning(request, f"Stage '{stage}' for LrNo '{track_id}' is already added.")
                else:
                    try:
                        Stages.objects.create(
                            Date=con_date,
                            Time=time_without_microseconds,
                            LrNo=track_id,
                            username=username,
                            Branch=branchname,
                            branchlocation=address,
                            stage=stage,
                        )
                        any_new_stages_saved = True  # Mark that a new stage was saved
                    except Exception as e:
                        # Notify the user about the error
                        messages.error(request, f"Error saving stage for track_id {track_id}: {e}")

            # Check if any new stages were saved and notify the user
            if any_new_stages_saved:
                messages.success(request, "New stages saved successfully.")

            # Redirect to the appropriate page after processing
            return redirect('stages')

        # If no stage is selected or no consignments are selected
        messages.error(request, 'No stage or consignments selected.')
        return render(request, 'stages.html')

    # If GET request, render form (adjust template as needed)
    return render(request, 'stage_form.html')

from django.db.models import Count, Q

def admin_dashboard(request):
    # Get the date from the POST request
    date = request.POST.get('date')

    # Filter consignments by the selected date
    if date:
        filtered_consignments = AddConsignment.objects.filter(date=date)
    else:
        filtered_consignments = AddConsignment.objects.all()

    # Group consignments by branch (in AddConsignment, it's 'branch')
    branch_consignments = filtered_consignments.values('branch').annotate(total_consignments=Count('id'))

    # Define the stage labels
    stage_labels = ['Picked', 'Staged at SD', 'In Transit', 'Staged at DD', 'Out for Delivery', 'Delivered']

    # Initialize an empty dictionary to store branch-wise stage counts
    branch_stage_counts = {branch['branch']: {label: 0 for label in stage_labels} for branch in branch_consignments}

    # Count consignments in each stage for each branch (use 'Branch' with capital 'B' here)
    stages_count = Stages.objects.filter(LrNo__in=filtered_consignments.values('track_id')).values('Branch', 'stage').annotate(stage_count=Count('id'))

    # Update branch-wise stage counts
    for stage in stages_count:
        if stage['stage'] in stage_labels:
            branch_stage_counts[stage['Branch']][stage['stage']] = stage['stage_count']

    # Count consignments not added to Stages table for each branch
    branch_untracked_consignments = filtered_consignments.filter(~Q(track_id__in=Stages.objects.values('LrNo'))).values('branch').annotate(untracked_count=Count('id'))

    # Prepare untracked consignments per branch
    untracked_counts = {branch['branch']: branch['untracked_count'] for branch in branch_untracked_consignments}

    # Prepare a list of branch data to pass to the template
    branches_data = []
    for branch in branch_consignments:
        branch_data = {
            'branch': branch['branch'],
            'total_consignments': branch['total_consignments'],
            'stage_counts': branch_stage_counts[branch['branch']],
            'untracked_consignments': untracked_counts.get(branch['branch'], 0),
        }
        branches_data.append(branch_data)

    context = {
        'branches_data': branches_data,
        'selected_date': date,
    }

    return render(request, 'admin_dashboard.html', context)

def branch_dashboard(request):
    # Get the date from the POST request
    date = request.POST.get('date')

    uid = request.session.get('username')
    uname = Branch.objects.get(email=uid)
    branch = uname.companyname

    # Filter consignments by the selected date (assuming consignment_date field exists)
    if date:
        filtered_consignments = AddConsignment.objects.filter(date=date,branch=branch)
    else:
        filtered_consignments = AddConsignment.objects.filter(branch=branch)

    # Count total consignments for the selected date
    total_consignments = filtered_consignments.count()

    # Count consignments in each stage for the selected date
    stages_count = Stages.objects.filter(LrNo__in=filtered_consignments.values('track_id')).values('stage').annotate(
        stage_count=Count('id'))

    # Define the stage labels
    stage_labels = ['Picked', 'Staged at SD', 'In Transit', 'Staged at DD', 'Out for Delivery', 'Delivered']

    # Prepare stage counts dictionary
    stage_counts = {label: 0 for label in stage_labels}

    # Update stage counts based on the retrieved data
    for stage in stages_count:
        if stage['stage'] in stage_labels:
            stage_counts[stage['stage']] = stage['stage_count']

    # Count consignments not added to Stages table for the selected date
    untracked_consignments = filtered_consignments.filter(~Q(track_id__in=Stages.objects.values('LrNo'))).count()

    context = {
        'total_consignments': total_consignments,
        'stage_counts': stage_counts,
        'untracked_consignments': untracked_consignments,
        'selected_date': date,
    }
    return render(request,'branch_dashboard.html',context)


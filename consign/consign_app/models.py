from django.db import models

class Login(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    name = models.CharField(max_length=50,null=True)
    utype = models.CharField(max_length=50)

class AddTrack(models.Model):
    track_id = models.CharField(max_length=50, null=True)
    date = models.CharField(max_length=30, null=True)
    description = models.CharField(max_length=30, null=True)
    branch=models.CharField(max_length=100,null=True)

class Branch(models.Model):
    headname = models.CharField(max_length=150, null=True)
    companyname = models.CharField(max_length=50, null=True)
    phonenumber = models.CharField(max_length=50, null=True)
    email = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=50, null=True)
    password = models.CharField(max_length=50, null=True)


class AddConsignment(models.Model):
    track_id = models.CharField(max_length=50, null=True)
    sender_name = models.CharField(max_length=50, null=True)
    sender_mobile = models.CharField(max_length=50, null=True)
    sender_address = models.CharField(max_length=50, null=True)
    sender_GST=models.CharField(max_length=50,null=True)
    receiver_name = models.CharField(max_length=50, null=True)
    receiver_mobile = models.CharField(max_length=50, null=True)
    receiver_address = models.CharField(max_length=50, null=True)
    receiver_GST = models.CharField(max_length=50, null=True)
    total_cost = models.FloatField(null=True)
    date = models.CharField(max_length=30, null=True)
    pay_status = models.CharField(max_length=30, null=True)
    route_from = models.CharField(max_length=30, null=True)
    route_to = models.CharField(max_length=30, null=True)
    pieces = models.IntegerField(null=True)
    prod_price = models.CharField(max_length=50,null=True)
    weight = models.FloatField(null=True)
    freight = models.FloatField(null=True)
    hamali = models.FloatField(null=True)
    door_charge = models.FloatField(null=True)
    Consignment_id=models.IntegerField(null=True)
    branch = models.CharField(max_length=150, null=True)
    name = models.CharField(max_length=150, null=True)
    time=models.CharField(max_length=50,null=True)
    copy_type = models.CharField(max_length=150, null=True)
    delivery = models.CharField(max_length=150, null=True)
    eway_bill =models.CharField(max_length=150, null=True)
    category = models.CharField(max_length=150, null=True)
    barcode_number = models.CharField(max_length=100, blank=True, null=True)  # To store the barcode number
    barcode_image = models.ImageField(upload_to='barcode/', blank=True, null=True)
    remark = models.CharField(max_length=150,null=True)
    gst = models.IntegerField(null=True)
    cgst = models.FloatField(null=True)
    sgst = models.FloatField(null=True)
    status = models.CharField(max_length=150,null=True)
    reason = models.CharField(max_length=150, null=True)


    def __str__(self):
        return self.track_id

class AddConsignmentTemp(models.Model):
    track_id = models.CharField(max_length=50, null=True)
    sender_name = models.CharField(max_length=50, null=True)
    sender_mobile = models.CharField(max_length=50, null=True)
    sender_address = models.CharField(max_length=50, null=True)
    sender_GST=models.CharField(max_length=50,null=True)
    receiver_name = models.CharField(max_length=50, null=True)
    receiver_mobile = models.CharField(max_length=50, null=True)
    receiver_address = models.CharField(max_length=50, null=True)
    receiver_GST = models.CharField(max_length=50, null=True)
    total_cost = models.FloatField(null=True)
    date = models.CharField(max_length=30, null=True)
    pay_status = models.CharField(max_length=30, null=True)
    route_from = models.CharField(max_length=30, null=True)
    route_to = models.CharField(max_length=30, null=True)
    pieces = models.IntegerField(null=True)
    prod_price = models.CharField(max_length=50,null=True)
    weight = models.FloatField(null=True)
    freight = models.FloatField(null=True)
    hamali = models.FloatField(null=True)
    door_charge = models.FloatField(null=True)
    Consignment_id=models.IntegerField(null=True)
    branch = models.CharField(max_length=150, null=True)
    name = models.CharField(max_length=150, null=True)
    time = models.CharField(max_length=50,null=True)
    copy_type = models.CharField(max_length=150,null=True)
    delivery = models.CharField(max_length=150, null=True)
    eway_bill =models.CharField(max_length=150, null=True)
    category = models.CharField(max_length=150, null=True)
    barcode_number = models.CharField(max_length=100, blank=True, null=True)  # To store the barcode number
    barcode_image = models.ImageField(upload_to='barcode/', blank=True, null=True)
    remark = models.CharField(max_length=150,null=True)
    gst = models.IntegerField(null=True)
    cgst = models.FloatField(null=True)
    sgst = models.FloatField(null=True)
    status = models.CharField(max_length=150, null=True)
    reason = models.CharField(max_length=150, null=True)



class ConsignmentHistory(models.Model):
    track_id = models.CharField(max_length=50, null=True)
    sender_name = models.CharField(max_length=50, null=True)
    sender_mobile = models.CharField(max_length=50, null=True)
    sender_address = models.CharField(max_length=50, null=True)
    receiver_name = models.CharField(max_length=50, null=True)
    receiver_mobile = models.CharField(max_length=50, null=True)
    receiver_address = models.CharField(max_length=50, null=True)
    total_cost = models.FloatField(null=True)
    date = models.CharField(max_length=30, null=True)
    pay_status = models.CharField(max_length=30, null=True)
    route_from = models.CharField(max_length=30, null=True)
    route_to = models.CharField(max_length=30, null=True)
    pieces = models.IntegerField(null=True)
    name = models.CharField(max_length=150, null=True)
    time = models.CharField(max_length=50,null=True)
    eway_bill =models.CharField(max_length=150, null=True)
    category = models.CharField(max_length=150, null=True)
    commit = models.CharField(max_length=150,null=True)




class Consignor(models.Model):
    sender_name = models.CharField(max_length=250, null=True)
    sender_mobile = models.CharField(max_length=250, null=True)
    sender_address = models.CharField(max_length=250, null=True)
    sender_GST=models.CharField(max_length=250,null=True)
    sender_password = models.CharField(max_length=250,null=True)
    branch=models.CharField(max_length=250,null=True)
    username = models.CharField(max_length=250, null=True)



class Consignee(models.Model):
    receiver_name = models.CharField(max_length=250, null=True)
    receiver_mobile = models.CharField(max_length=250, null=True)
    receiver_address = models.CharField(max_length=250, null=True)
    receiver_GST = models.CharField(max_length=250, null=True)
    receiver_password =models.CharField(max_length=250, null=True)
    branch=models.CharField(max_length=250,null=True)
    username = models.CharField(max_length=250, null=True)

class Parties(models.Model):
    route_from = models.CharField(max_length=30, null=True)
    route_to = models.CharField(max_length=30, null=True)
    sender_name = models.CharField(max_length=50, null=True)
    sender_mobile = models.CharField(max_length=50, null=True)
    sender_address = models.CharField(max_length=50, null=True)
    sender_GST = models.CharField(max_length=50, null=True)
    receiver_name = models.CharField(max_length=50, null=True)
    receiver_mobile = models.CharField(max_length=50, null=True)
    receiver_address = models.CharField(max_length=50, null=True)
    receiver_GST = models.CharField(max_length=50, null=True)
    branch=models.CharField(max_length=50,null=True)




class FeedBack(models.Model):
    username=models.CharField(max_length=50,null=True)
    feedback=models.CharField(max_length=200,null=True)
    def __str__(self):
        return self.username


class Vehicle(models.Model):
    vehicle_number = models.CharField(max_length=50, null=True)


class Driver(models.Model):
    driver_name = models.CharField(max_length=50, null=True)
    phone_number = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=50, null=True)
    passport = models.CharField(max_length=50, null=True)
    license = models.CharField(max_length=50, null=True)

class Location(models.Model):
    location = models.CharField(max_length=150, null=True)

class Staff(models.Model):
    staffname = models.CharField(max_length=150, null=True)
    staffPhone = models.CharField(max_length=150, null=True)
    staffaddress = models.CharField(max_length=150, null=True)
    aadhar = models.CharField(max_length=150, null=True)
    staffid = models.CharField(max_length=150, null=True)
    Branch = models.CharField(max_length=150, null=True)
    passbook = models.CharField(max_length=150, null=True)
    passbookphoto = models.CharField(max_length=150, null=True)
    passport = models.CharField(max_length=150, null=True)

class TripSheetPrem(models.Model):
    DriverName=models.CharField(max_length=150,null=True)
    VehicalNo=models.CharField(max_length=150,null=True)
    AdvGiven=models.CharField(max_length=150,null=True)
    Time=models.TimeField(null=True)
    Date=models.DateField(null=True)
    LRno=models.IntegerField(null=True)
    qty=models.FloatField(null=True)
    category=models.CharField(max_length=150,null=True)
    dest=models.CharField(max_length=150,null=True)
    consignee=models.CharField(max_length=150,null=True)
    username=models.CharField(max_length=150,null=True)
    pay_status = models.CharField(max_length=150, null=True)
    branch=models.CharField(max_length=150,null=True)
    total_cost = models.FloatField(null=True)
    freight = models.FloatField(null=True)
    hamali = models.FloatField(null=True)
    door_charge = models.FloatField(null=True)
    trip_id =models.CharField(max_length=150,null=True)
    weight = models.FloatField(null=True)
    prod_price = models.FloatField(null=True)



class TripSheetTemp(models.Model):
    Date=models.DateField(null=True)
    LRno=models.IntegerField(null=True)
    qty=models.FloatField(null=True)
    category=models.CharField(max_length=150,null=True)
    dest=models.CharField(max_length=150,null=True)
    consignee=models.CharField(max_length=150,null=True)
    username=models.CharField(max_length=150,null=True)
    pay_status = models.CharField(max_length=150, null=True)
    branch = models.CharField(max_length=150, null=True)
    total_cost=models.FloatField( null=True)
    freight = models.FloatField(null=True)
    hamali = models.FloatField(null=True)
    st_charge = models.FloatField(null=True)
    door_charge = models.FloatField(null=True)
    weight = models.FloatField(null=True)
    prod_price = models.FloatField(null=True)


class Account(models.Model):
    Date = models.CharField(max_length=50, null=True)
    track_number = models.CharField(max_length=50)
    debit = models.CharField(max_length=50, null=True)
    credit = models.CharField(max_length=50, null=True)
    Balance = models.CharField(max_length=50, null=True)
    sender_name = models.CharField(max_length=255)
    TrType = models.CharField(max_length=50, null=True)
    particulars = models.CharField(max_length=50, null=True)
    headname = models.CharField(max_length=50, null=True)
    Branch=models.CharField(max_length=150,null=True)


class Expenses(models.Model):
    Date=models.CharField(max_length=150,null=True)
    Reason=models.CharField(max_length=150,null=True)
    Amount=models.CharField(max_length=150,null=True)
    branch=models.CharField(max_length=150,null=True)
    username=models.CharField(max_length=150,null=True)
    staffname = models.CharField(max_length=150, null=True)


class Category(models.Model):
    cat_name=models.CharField(max_length=150,null=True)
    prefix = models.CharField(max_length=150, null=True)
    freight = models.FloatField(null=True)


class Disel(models.Model):
    Date = models.CharField(max_length=50, null=True)
    vehicalno = models.CharField(max_length=50, null=True)
    drivername = models.CharField(max_length=50, null=True)
    ltrate = models.FloatField(max_length=50, null=True)
    liter = models.FloatField(max_length=50, null=True)
    total = models.FloatField(max_length=50, null=True)
    trip_id = models.FloatField(max_length=50, null=True)

class Stages(models.Model):
    Date = models.DateField(null=True)
    Time = models.CharField( max_length=250,null=True)
    LrNo = models.CharField(max_length=150,null=True)
    stage = models.CharField(max_length=150,null=True)
    username = models.CharField(max_length=150,null=True)
    Branch = models.CharField(max_length=150, null=True)
    branchlocation = models.CharField(max_length=150,null=True)
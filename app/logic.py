import datetime as datetime
import calendar
from decimal import ROUND_HALF_UP, Decimal
from peewee import fn
#from dateutil.relativedelta import relativedelta, MO
from models import db,Transaction_Ledger as t, Loan as l, Borrower as b, Member as m, Loan_Repayment as r

db.connect()

def get_loan_record_by_ID(input_ID):
    try:
        record = l.get_by_id(input_ID)
    except l.DoesNotExist:
        print(f"Loan {input_ID} not found")
        return
    return record
    
def days_in_year(year):
    return 365 + calendar.isleap(year)

def round_half_up(decimal_num):
    str_num = str(decimal_num)
    return Decimal(str_num).quantize(Decimal('0.01'),ROUND_HALF_UP)

def total_fund_value():
    
    ledger_sum = t.select(fn.sum(t.amount)).scalar()
    active_loan = l.select(fn.sum(l.principal)).where(l.status=='pd').scalar()

    total_fund_value = ledger_sum + active_loan
    return total_fund_value

def check_total_stake():
    total_stake = m.select(fn.sum(m.stake)).where(m.is_active==True).scalar()
    if total_stake != 1.00:
        print(f"Warning: Stake is not 100%. >> {total_stake} ") 
        return False
    else:
        return True

def calculate_interest(loan_id,payment_date=None):

    loan = get_loan_record_by_ID(loan_id)

    if payment_date is None:
        loan_days= (datetime.date.today() - loan.lending_date).days
    else:
        loan_days = (payment_date - loan.lending_date).days

    loan_interest = loan.principal * loan.interest_rate * max(0,loan_days)/ days_in_year(loan.lending_date.year)
    return round_half_up(loan_interest)

def calculate_required_payment(loan_id,target_reduction,date=None):
    loan = get_loan_record_by_ID(loan_id)
    interest_needed = calculate_interest(loan.id)

    total_required = target_reduction+interest_needed
    return { 'interest': interest_needed,
            'reduction': round_half_up(target_reduction),
            'total': round_half_up(total_required)}

def get_member_shares(member_id):
    if check_total_stake() == True:
        try:
            member = m.get_by_id(member_id)
        except m.DoesNotExist:
            print(f"Member {member_id} not found")
            return
        
        share = Decimal.from_float(total_fund_value()) * member.stake   
        return round_half_up(share)

def check_loan_status(loan_id,date_receive_payment=None):

    loan = get_loan_record_by_ID(loan_id)
    
    if loan.principal == 0 and not loan.status == 'cl': #close loan
        loan.update(status='cl',actual_payback_date=date_receive_payment).where(l.id==loan_id).execute()
        
    elif not loan.principal == 0 and loan.plan_payback_date < datetime.date.today(): #overdue
        loan.update(status='od').where(l.id==loan_id).execute()
     
    else:
        loan.update(status='pd').where(l.id==loan_id).execute()

def record_payment(loan_id,amount_paid,date_received):
    loan = get_loan_record_by_ID(loan_id)
    
    accrued_int = calculate_interest(loan.id,date_received)

    interest_portion = min(amount_paid,accrued_int)

    with db.atomic():
        payment_type = 'i'
        principal_reduction =  round_half_up(amount_paid - interest_portion)  #amount to minus principal  
        if loan.principal - principal_reduction < 0:   
            print(f"{principal_reduction} is more than principal: {loan.principal}")
            return

        if interest_portion > 0: #only interest
            t.insert(member=4, amount=interest_portion, category='loan_int_received',loan_id=loan_id).execute()
            payment_type = 'i'
        if principal_reduction > 0: #have balance for principal    
            new_principal = round_half_up(loan.principal - principal_reduction)
            l.update(principal=new_principal).where(l.id ==loan_id).execute()
            t.insert(member=4, amount=principal_reduction, category='principal_returned',loan_id=loan_id).execute()
            payment_type = 'p'
        if amount_paid > accrued_int:
            l.update(lending_date = date_received).where(l.id==loan_id).execute()
            date_obj = datetime.date(date_received)
            new_payback_date = date_obj.year + 1
        #save payment in loan repayment
        if payment_type:
            r.insert(loan=loan.id, amount_paid=amount_paid, date=date_received, payment_type=payment_type).execute()
        check_loan_status(loan.id,date_received)



db.close()


    
    
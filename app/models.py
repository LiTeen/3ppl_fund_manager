import peewee as pw
import datetime 

db = pw.SqliteDatabase('fund.db')

class BaseModel(pw.Model):
    class Meta: 
        database = db


class Member(BaseModel):
    name = pw.CharField(max_length=100, unique=True)
    initial_capital = pw.DecimalField(max_digits=12, decimal_places=2)
    join_date = pw.DateField()
    stake = pw.DecimalField(max_digits=3, decimal_places=2)
    is_active = pw.BooleanField(default=True)


class Borrower(BaseModel):
    name = pw.CharField(max_length=100,  unique=True)


class Loan(BaseModel):
    borrower = pw.ForeignKeyField(Borrower, backref='loans')
    principal = pw.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = pw.DecimalField(default=0.03, max_digits=3,decimal_places=2)
    lending_date = pw.DateField()
    plan_payback_date = pw.DateField()
    actual_payback_date = pw.DateField(null=True)

    STATUS_CHOICES = (
        ('pd','Pending'),
        ('pe','Paid Early'),
        ('od','Overdue'),
        ('cl','Closed')
    )
    status = pw.CharField(default='pd', max_length=2, choices=STATUS_CHOICES)


class Transaction_Ledger(BaseModel):
    member = pw.ForeignKeyField(Member,backref='transactions')
    amount = pw.DecimalField(max_digits=12,decimal_places=2)
    timestamp = pw.DateTimeField(default = datetime.datetime.now)
    loan_id = pw.ForeignKeyField(Loan,backref='loan_reference',null=True)
    remarks = pw.CharField(max_length=300,null=True)
    
    CATEGORY_CHOICES = (
        ('capital_withdraw', 'Capital Withdrawal'),
        ('bank_int_received', 'Bank Interest Received'),
        ('loan_out', 'Loan Out'),
        ('principal_returned','Principal Returned'),
        ('loan_int_received','Loan Interest Received'),
        ('capital_in', 'Capital Injection')
    )
    category = pw.CharField(max_length=30,choices=CATEGORY_CHOICES)


class Loan_Repayment(BaseModel):
    loan = pw.ForeignKeyField(Loan, backref='repayments')
    amount_paid = pw.DecimalField(max_digits=12,decimal_places=2)
    date = pw.DateField()
    remarks = pw.CharField(max_length=300,null=True)
    PAYMENT_CHOICES = (
        ('i','Interest only'),
        ('p','Principal reduction')
    )

    payment_type = pw.CharField(max_length=1 , choices = PAYMENT_CHOICES,default = 'p')
    
## run connection execute

if __name__ == '__main__':
    db.connect()
    db.create_tables([Member,Borrower,Loan,Transaction_Ledger,Loan_Repayment],safe=True)
    db.close()
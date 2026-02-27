from models import Loan 
import logic as l
from decimal import Decimal 
from datetime import date


#test function
def test(session):
    loan = session.get(Loan,3)
    if Loan:
        loan.lending_date = date(2024,2,29)

        session.commit()
        session.refresh(loan)


        
#l.record_payment(3,Decimal(110.15),datetime.date(2026,12,2))
#m.insert(name='General Fund',initial_capital=0.00,join_date='2023-07-03',stake=0.00,is_active=False)
#models.Loan.update(lending_date='2024-02-29').where(models.Loan.id == 3).execute()
#l.check_loan_status(3)
#models.Loan.create(borrower=1,
        #  principal=30000.00,
        #  lending_date='2023-12-01',
        #  plan_payback_date='2024-12-01',
        #  status='pd')
# principal = models.Loan.select(models.Loan.principal).where(models.Loan.id == 7).scalar()
# new_total_owe = l.calculate_interest(7,datetime.date(2026,12,1)) + principal 

# print(new_total_owe)

#print(l.calculate_required_payment(3,Decimal(110.14),datetime.date(2026,12,2)))
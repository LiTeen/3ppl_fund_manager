1. Member Model 
    - Member Name: [Teen, Jacky, WCH]
    - Initial capital: [RM 53,081.42] | 21232.57, 21232.57,10616.28
    - Join Date: [3/7/2023]
    - Stake: [0.4,0.4,0.2]
    - Is Active: If the fund ever changes members, you can "deactivate" one without deleting their historical data.

2. Borrower Model 
    - Borrower Name

3. Loan Model(The 3% Simple Interest)
    - Borrower Link: Foreign key to the borrower model
    - Principal: The original amount lent
    - Annual Interest Rate: [0.03]
    - Lending date: When the money left the fund
    - Plan payback date: What borrower promised
    - Actual payback date: [Allow NULL] When payback money received
    - Status:(eg: Pending-PD, Paid_Early-PE, Overdue-OD, Closed-CL)

4. Transaction Ledger
    - Member link: Who is this for?
    - Amount: Positive for money in, Negative for money out
    - Category: Capital Withdrawal / Bank Interest Received / Loan Out/ Principal Returned / Loan Interest Received / Capital Injection
    - Timestamp: Exact date of the entry
    - Reference ID: (Optional: Link to a Loan ID if applicable, or leave empty for Bank Interest)
    - Remarks: "6 months HLB @ 3.5%"

5. Loan Repayment Model 
    - Loan Link: Which loan is paid
    - Amount Paid: Money received
    - Payment Type: Interest only / Principal reduction
    - Date: When the payment was received?
    - Remarks: Reason for borrow

   
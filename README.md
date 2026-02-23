# 3ppl_fund_manager

## Purpose

Private internal application to manage a jointly owned inherited fund and record lending activity.

This system tracks:

* Capital allocation
* Loan issuance
* Simple interest calculation (3% p.a.)
* Repayments
* Beneficiary share value

For internal use only.

---

## Ownership Structure

| Beneficiary | Allocation |
| ----------- | ---------- |
| Member 1    | 40%        |
| Member 2    | 40%        |
| Member 3    | 20%        |

Ownership percentages are fixed unless manually adjusted.

---

## Lending Rules

* Loans issued to close relatives only
* Fixed interest rate: **3% per annum (simple interest)**
* No compounding
* Interest formula:

  ```
  Interest = Principal × 0.03 × Days of borrow / Days in a year
  ```

---

## Core Features

### Fund Management

* Record initial capital
* Track available cash
* Track outstanding principal
* Compute total fund value

### Loan Records

* Borrower name
* Principal amount
* Start date
* Duration
* Status (active / repaid)
* Repayment history

### Interest Tracking

* Accrued interest calculation
* Outstanding balance per loan
* Total interest earned

### Reporting

* Total fund value (cash + loans + interest)
* Individual share value based on 40/40/20 allocation
* Transaction history log

---

## System Scope

* Single private user
* No multi-user authentication required
* No external integrations
* Focused on accuracy and transparency
* Minimal UI, backend-driven logic

---

## Non-Goals

* Not a public financial product
* No regulatory handling
* No complex accounting standards
* No compounding or variable interest rates

---

## Long-Term Objective

Maintain transparent, structured records of:

* Capital preservation
* Interest income
* Fair beneficiary allocation
* Historical loan activity

---

Refactoring Notes (Q1)
Overview

This document summarizes the issues in legacy_ledger.py and the fixes implemented in legacy_fixed.py to meet security, performance, and data-integrity requirements.

1. Issues in Legacy Code

A)Security – SQL Injection:
i)Search queries were built using f-strings.
ii)Allowed attackers to retrieve unauthorized data using crafted inputs(e.g. : ' OR '1'='1).

B)Performance – Blocking I/O:

i)time.sleep(3) blocked request handling.
ii)Concurrent requests were processed sequentially.

C)Data Integrity – Unsafe Updates:

i)Balance updates were not atomic.
ii)No validation for sufficient funds before deduction.

2. Refactored Solution (legacy_ledger_Fixed.py)

The service was rewritten using FastAPI while preserving the original database initialization logic.

A)Security Hardening:

i)Used parameterized SQL queries.
ii)Eliminated SQL injection vulnerabilities.

B)Performance Optimization

i)Adopted async/await architecture.
ii)Replaced blocking sleep with asyncio.sleep, keeping the API responsive.

C)Data Integrity

i)Wrapped balance updates in database transactions.
ii)Validated balance before update and rolled back on failure.

3. Verification

A pytest suite (test_legacy_ledger_Fixed.py) validates the fixes:

i)SQL injection attempts fail.
ii)Concurrent transactions execute in parallel.
iii)Failed transactions do not modify balances.

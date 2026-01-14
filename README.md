Project-1:

This file gives you a hands on, on how to execute each questions.

Question 1:

You can either run the legacy_ledger_fixed.py file and run curl cmds to check for the vulnerabilities or directly run the test file: test_legacy_ledger_Fixed.py (pytest test_legacy_ledger_Fixed.py -v), which tries three different vulnerability checks(Aligns with the requirements mentioned).

Question 2:

Run the app.py file to get the server running and then run the locust file(load_test.py) in another terminal. Open a new terminal and run the simulate_outage.py file which locks the database, but the server keeps running and accepts requests. To check if the database is locked you can run a sqlite cmd in a new terminal(gives a msg stating the db is locked).

Question 3:

Run the app.py(creates new db with the items), and then run the proof_of_concurrency.py in another terminal, which shows 4 different metrics, Successful Buys (200 OK), Sold Out Responses (410 GONE), Busy / Timeout Responses (503) and Errors. 

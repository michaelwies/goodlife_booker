@echo off
SET days = %1
SET slot = %2
IF "%~1" == "" (
    ECHO Input Values Required.
	ECHO "Parameter 1 = Days from now to book (0-6)"
	ECHO "Parameter 2 = Index of Slot to book (1-n)"
	exit /b 1
)
python "C:\Users\mwies\Documents\git\goodlife_booker\booking_script.py"  --days %1 --slot %2
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python booking_script.py  --dry --days 6 --slot 1
deactivate

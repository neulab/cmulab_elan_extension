@echo off

set PYTHONLEGACYWINDOWSIOENCODING=True
set PYTHONIOENCODING=:replace

If not exist venv\ (
  echo "PROGRESS: 1% Initial setup: Creating virtual env, installing dependencies"
  python3 -m venv venv
  call .\venv\Scripts\activate
  python3 -m pip --no-input install -r requirements.txt
  echo "PROGRESS: 5% One-time initialization successfully completed!"
  call deactivate
)

echo "Activating venv..."
call .\venv\Scripts\activate
python3 .\cmulab_elan_extension.py
call deactivate

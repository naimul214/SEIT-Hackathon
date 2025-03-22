## general information 
# activating and deactivating the venv
- source .venv/bin/activate
- deactivate

# activating the application manually from inside the venv
- uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# find the PIDs for uvicorn
- ps aux | grep "uvicorn"

# kill the server 
- ctrl + c

# if ctrl + c doesnt work for some reason
- kill <PID>

# todo
- impliment a makefile for graceful start up, shutdown, and cache clear of the app
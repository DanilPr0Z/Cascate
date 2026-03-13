"""
Gunicorn configuration file for Mebel project
"""

import multiprocessing

# Bind to Unix socket or TCP port
bind = "unix:/var/www/mebel/mebel.sock"
# Alternatively, bind to TCP port:
# bind = "0.0.0.0:8000"

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "sync"

# Timeout for requests (seconds)
timeout = 120

# Maximum number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/www/mebel/logs/gunicorn_access.log"
errorlog = "/var/www/mebel/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "mebel"

# Daemon mode (set to True if not using systemd)
daemon = False

# User and group to run as (optional, use with systemd)
# user = "www-data"
# group = "www-data"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

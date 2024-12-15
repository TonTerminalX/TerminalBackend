import multiprocessing
import os

bind = "0.0.0.0:8000"

workers = multiprocessing.cpu_count() * 2 + 1

worker_class = "sync"

timeout = 30

max_requests = 1000
max_requests_jitter = 50

loglevel = "info"
accesslog = "-"
errorlog = "-"

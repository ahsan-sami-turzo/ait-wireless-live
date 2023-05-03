#!/bin/bash

celery -A Notifier.celery multi start "general1" --time-limit=300 --autoscale=6,1 --queues="general1" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "general2" --time-limit=300 --autoscale=6,1 --queues="general2" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "general3" --time-limit=300 --autoscale=6,1 --queues="general3" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "general4" --time-limit=300 --autoscale=6,1 --queues="general4" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "general5" --time-limit=300 --autoscale=6,1 --queues="general5" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"

celery -A Notifier.celery multi start "priority1" --pool=gevent --concurrency=10 --queues="priority1" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "priority2" --pool=gevent --concurrency=10 --queues="priority2" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "priority3" --pool=gevent --concurrency=10 --queues="priority3" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "priority4" --pool=gevent --concurrency=10 --queues="priority4" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "priority5" --pool=gevent --concurrency=10 --queues="priority5" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"

celery -A Notifier.celery multi start "micro1" --pool=gevent --concurrency=10 --queues="micro1" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "micro2" --pool=gevent --concurrency=10 --queues="micro2" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "micro3" --pool=gevent --concurrency=10 --queues="micro3" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "micro4" --pool=gevent --concurrency=10 --queues="micro4" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "micro5" --pool=gevent --concurrency=10 --queues="micro5" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "micro6" --pool=gevent --concurrency=10 --queues="micro6" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "micro7" --pool=gevent --concurrency=10 --queues="micro7" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "micro8" --pool=gevent --concurrency=10 --queues="micro8" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "micro9" --pool=gevent --concurrency=10 --queues="micro9" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "micro10" --pool=gevent --concurrency=10 --queues="micro10" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"

celery -A Notifier.celery multi start "update1" --pool=gevent --concurrency=10 --queues="update1" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "update2" --pool=gevent --concurrency=10 --queues="update2" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"
celery -A Notifier.celery multi start "update3" --pool=gevent --concurrency=10 --queues="update3" --pidfile="/var/lib/celery/%n.pid" --logfile="/var/lib/celery/log/%n%I.log" --loglevel="ERROR"

celery -A Notifier.celery worker --loglevel=ERROR --concurrency=1
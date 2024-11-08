##!/bin/sh
#while !</dev/tcp/$POSTGRES_HOST/5432; do sleep 1; done;
#sleep 3;
#
python manage.py migrate --no-input;
#exec gunicorn -c "docker/gunicorn.config.py" "core.wsgi:application";
exec python manage.py runserver 0.0.0.0:8000;
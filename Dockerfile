FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY pyproject.toml /code/
COPY poetry.lock /code/

RUN pip install --upgrade pip setuptools wheel
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY . .

ENV PORT=8000

EXPOSE $PORT

CMD ["python", "manage.py", "migrate", "--noinput"]
#CMD ["gunicorn", "-c", "docker/gunicorn.config.py", "core.wsgi:application"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


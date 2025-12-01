# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3-slim

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set a default SECRET_KEY for Django (should be overridden in production)
ENV SECRET_KEY='django-insecure-docker-default-key-change-in-production'

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Run Django migrations and collectstatic before switching to non-root user
RUN python /app/tutorial/manage.py migrate --noinput && \
    python /app/tutorial/manage.py collectstatic --noinput

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Set working directory to the Django project directory
WORKDIR /app/tutorial

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "tutorial.wsgi"]

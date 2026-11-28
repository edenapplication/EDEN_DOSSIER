FROM python:3.11

# Empêche Python d'écrire les fichiers .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Empêche la bufferisation des logs (important pour Docker)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

# ✅ Gunicorn au lieu de runserver
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--worker-class", "gthread", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
FROM python:3.8

# Running as root (security issue)
USER root

# Hardcoded credentials (security issue)
ENV DB_PASSWORD=mysecretpassword123

# Installing without version pinning
RUN pip install flask requests

# Exposing all ports
EXPOSE 22 80 443 8080

COPY . /app
WORKDIR /app

CMD ["python", "app.py"]

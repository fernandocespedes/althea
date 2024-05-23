FROM python:3.12
LABEL maintainer="althea.com"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY . /althea
WORKDIR /althea
EXPOSE 8000

ARG DEV=false

# Set up Python environment
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip

# Install system dependencies
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    apt-get install -y --no-install-recommends build-essential libpq-dev

# Install Python dependencies
RUN /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; then \
        /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi

# Clean up to reduce image size
RUN apt-get remove -y build-essential libpq-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    find /tmp -mindepth 1 -delete

# Add a user for the application
RUN adduser --disabled-password --no-create-home django-user

# Set up media and static directories
RUN mkdir -p /althea/media && \
    mkdir -p /althea/static && \
    chown -R django-user:django-user /althea/media /althea/static /althea

# Add the virtual environment binaries to PATH
ENV PATH="/py/bin:$PATH"

# Switch to the non-root user
USER django-user



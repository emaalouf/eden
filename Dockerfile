# Use an Ubuntu base image
FROM ubuntu:18.04

# Set environment variables to prevent interactive prompts during the build
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    unzip \
    curl \
    python \
    python-dev \
    python-pip \
    python-matplotlib \
    python-lxml \
    python-numpy \
    python-dateutil \
    python-gdal \
    python-yaml \
    python-serial \
    python-xlwt \
    python-shapely \
    python-pil \
    python-reportlab \
    python-tweepy \
    python-xlrd \
    python-boto \
    ansible \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to ensure compatibility with modern Python packages
RUN pip install --upgrade pip

# Install required Python packages via pip (for Python 2)
RUN pip install selenium>=2.23.0 \
    sunburnt>=0.6 \
    TwitterSearch>=1.0 \
    requests>=2.3.0 \
    Django==2.2.24 \   # Ensure compatibility with Django and web2py
    wtforms==2.3.3     # If you are using WTForms for form validation

# Download and extract the web2py version compatible with Python 2
RUN curl -o web2py.zip https://codeload.github.com/web2py/web2py/zip/R-2.9.11 && unzip web2py.zip \
    && mv web2py-R-2.9.11 /home/web2py && rm web2py.zip

# Copy the SahanaEden application code into the correct location within web2py
COPY . /home/web2py/applications/eden

# Modify the SahanaEden configuration file (if needed)
RUN cp /home/web2py/applications/eden/modules/templates/000_config.py /home/web2py/applications/eden/models/000_config.py \
    && sed -i 's|EDITING_CONFIG_FILE = False|EDITING_CONFIG_FILE = True|' /home/web2py/applications/eden/models/000_config.py

# Expose the web server port (web2py runs on port 8000 by default)
EXPOSE 8000

# Set the Python path to make sure web2py finds all required modules
ENV PYTHONPATH=/home/web2py/

# Set the admin password as an environment variable
ENV WEB2PY_PASSWORD="p@Ssw0rd@221"

# Set the command to run the web2py server (using Python 2) on port 8000 with the admin password
CMD ["python", "/home/web2py/web2py.py", "-i", "0.0.0.0", "-p", "8000", "-a", "p@Ssw0rd@221"]

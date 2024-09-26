# Use an Ubuntu base image
FROM ubuntu:18.04

# Set environment variables to prevent interactive prompts during the build
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    unzip \
    curl \
    python3 \
    python3-dev \
    python3-pip \
    python3-matplotlib \
    python3-lxml \
    python3-numpy \
    python3-dateutil \
    python3-gdal \
    python3-yaml \
    python3-serial \
    python3-shapely \
    python3-pil \
    python3-reportlab \
    python3-tweepy \
    python3-xlrd \
    python3-boto \
    ansible \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to ensure compatibility with modern Python packages
RUN python3 -m pip install --upgrade pip

# Install required Python packages via pip (for Python 3)
RUN pip3 install "selenium>=2.23.0" "sunburnt>=0.6" "TwitterSearch>=1.0" "requests>=2.3.0" "Django==3.2.13" "wtforms==2.3.3" "xlwt>=1.3.0"

# Download and extract the web2py version compatible with Python 3
RUN curl -o web2py.zip https://codeload.github.com/web2py/web2py/zip/R-2.21.1 && unzip web2py.zip \
    && mv web2py-R-2.21.1 /home/web2py && rm web2py.zip

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

# Set the command to run the web2py server (using Python 3) on port 8000 with the admin password
CMD ["python3", "/home/web2py/web2py.py", "-i", "0.0.0.0", "-p", "8000", "-a", "p@Ssw0rd@221"]

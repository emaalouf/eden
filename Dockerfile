FROM ubuntu:18.04

ARG DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && apt-get install -y build-essential unzip curl python3-pip python3-dev python3-matplotlib \
    python3-lxml python3-numpy python3-dateutil python3-gdal python3-yaml python3-serial python3-shapely \
    python3-pil python3-reportlab python3-tweepy python3-boto ansible \
    && rm -rf /var/lib/apt/lists/*

# Install xlwt via pip3
RUN pip3 install xlwt


# Install Python libraries via pip
RUN pip3 install selenium>=2.23.0 sunburnt>=0.6 TwitterSearch>=1.0 requests>=2.3.0

# Download and set up web2py
RUN curl -o web2py.zip https://codeload.github.com/web2py/web2py/zip/R-2.9.11 && unzip web2py.zip \
    && mv web2py-R-2.9.11 /home/web2py && rm web2py.zip

# Copy the SahanaEden application code to web2py's applications directory
COPY . /home/web2py/applications/eden

# Update configuration for SahanaEden
RUN cp /home/web2py/applications/eden/modules/templates/000_config.py /home/web2py/applications/eden/models/000_config.py \
    && sed -i 's|EDITING_CONFIG_FILE = False|EDITING_CONFIG_FILE = True|' /home/web2py/applications/eden/models/000_config.py

# Expose the port
EXPOSE 8000

# Run the web2py server
CMD ["python3", "/home/web2py/web2py.py", "-i", "0.0.0.0", "-p", "8000", "-a", "eden"]

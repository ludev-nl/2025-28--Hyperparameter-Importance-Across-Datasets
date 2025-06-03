# Basic setup
FROM python:3.12
WORKDIR /usr/local/app

# Install PCRE, Redis, and SWIG
RUN apt-get update
    apt-get install -y libpcre3-dev redis-server
    wget -O swig.tar.gz https://sourceforge.net/projects/swig/files/swig/swig-3.0.12/swig-3.0.12.tar.gz/download
    tar -zxf swig.tar.gz
    cd swig-3.0.12 && ./configure && make && make install && cd ..
    rm -r swig-3.0.12 swig-3.0.12.tar.gz

# Install Python packages
COPY requirements/deploy.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy in the source code
# TODO: this should only copy in real source files
COPY . .

# Expose the port gunicorn runs on
EXPOSE 8000/tcp

# Run supervisord
CMD ["supervisord", "-c", "/usr/local/app/supervisord.conf"]

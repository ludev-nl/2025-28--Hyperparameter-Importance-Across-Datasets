# Basic setup
FROM python:3.12
WORKDIR /usr/local/app

# Install PCRE and Redis
RUN apt-get update &&\
    apt-get install -y libpcre3-dev redis-server

# Install SWIG
RUN wget -O swig-3.0.12.tar.gz https://sourceforge.net/projects/swig/files/swig/swig-3.0.12/swig-3.0.12.tar.gz/download &&\
    tar -zxf swig-3.0.12.tar.gz &&\
    cd swig-3.0.12 && ./configure && make && make install && cd .. &&\
    rm -r swig-3.0.12 swig-3.0.12.tar.gz

# Copy in the source code (see .dockerignore)
COPY . .

# Install Python packages
RUN pip install --no-cache-dir -r docs/deploy.txt

# Expose the port gunicorn runs on
EXPOSE 8000/tcp

# Run supervisord
CMD ["supervisord", "-n", "-c", "./docs/supervisord.conf"]

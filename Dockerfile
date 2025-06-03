# Basic setup
FROM python:3.12
WORKDIR /usr/local/app

# Install PCRE, Redis, and SWIG
RUN apt-get update
RUN apt-get install -y libpcre3-dev redis-server
RUN wget -O swig.tar.gz https://sourceforge.net/projects/swig/files/swig/swig-3.0.12/swig-3.0.12.tar.gz/download
RUN tar -zxf swig.tar.gz
WORKDIR swig-3.0.12
RUN ./configure && make && make install
WORKDIR ..
# TODO: try in the end if this reduces container size
# RUN rm -r swig-3.0.12

# Install Python packages
# TODO: this file structure will change
COPY freeze.txt freeze.txt
RUN pip install --no-cache-dir -r freeze.txt

# Copy in the source code
# TODO: this should only copy in real source files
COPY . .

# Expose the port gunicorn runs on
EXPOSE 8000/tcp

# Run supervisord
CMD ["supervisord", "-n", "-c", "/usr/local/app/supervisord.conf"]

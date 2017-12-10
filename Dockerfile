FROM clowder/pyclowder:2

MAINTAINER Ward Poelmans <wpoely86@gmail.com>

# Setup environment variables. These are passed into the container. You can change
# these to your setup. If RABBITMQ_URI is not set, it will try and use the rabbitmq
# server that is linked into the container. MAIN_SCRIPT is set to the script to be
# executed by entrypoint.sh
# REGISTRATION_ENDPOINTS should point to a central clowder instance, for example it
# could be https://clowder.ncsa.illinois.edu/clowder/api/extractors?key=secretKey
ENV RABBITMQ_URI="" \
    RABBITMQ_EXCHANGE="clowder" \
    RABBITMQ_QUEUE="ncsa.urlextractor" \
    REGISTRATION_ENDPOINTS="https://clowder.ncsa.illinois.edu/extractors" \
    MAIN_SCRIPT="url-extractor.py" \
    SELENIUM_URI="http://localhost:4444/wd/hub"

# Install any programs needed
RUN apt-get update && apt-get install -y python-pip && \
     rm -rf /var/lib/apt/lists/*

RUN pip install selenium requests lxml beautifulsoup4

# Switch to clowder, copy files and be ready to run
USER clowder

# command to run when starting docker
COPY entrypoint.sh *.py extractor_info.json /home/clowder/
RUN mkdir /home/clowder/config
COPY config /home/clowder/config
ENTRYPOINT ["/home/clowder/entrypoint.sh"]
CMD ["extractor"]

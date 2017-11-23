This is a [Clowder](https://clowder.ncsa.illinois.edu) extractor for URLs. It will create a thumbnail
every website giving to it. For this is will use selenium and chrome.

# Selenium

You need a running selenium instance. Using docker:
```
docker run -e SCREEN_WIDTH=1920 -e SCREEN_HEIGHT=1080 -p 4444:4444 selenium/standalone-chrome:3.7.1-beryllium
```
The environment variable `SELENIUM_URI` should point to the location of the selenium instance. By default
it points to: `http://localhost:4444/wd/hub`.

# Input format

It expects JSON input:
```json
{
    "URL": "https://clowder.ncsa.illinois.edu/"
}
```

# Metadata format

The extractor will generate following metadata:
```json
{
    "URL": "https://clowder.ncsa.illinois.edu/",
    "date": "2017-11-23T20:58:05.799474",
    "title": "Clowder - Research Data Management in the Cloud"
}
```

# Docker

This extractor is ready to be run as a docker container. To build the docker container run:

```
docker build -t clowder_urlextractor .
```

To run the docker containers use:

```
docker run -t -i --rm -e "RABBITMQ_URI=amqp://rabbitmqserver/clowder" clowder_urlextractor
docker run -t -i --rm --link clowder_rabbitmq_1:rabbitmq clowder_urlextractor
```

The RABBITMQ_URI and RABBITMQ_EXCHANGE environment variables can be used to control what RabbitMQ server and exchange it will bind itself to, you can also use the --link option to link the extractor to a RabbitMQ container.

This is a [Clowder](https://clowder.ncsa.illinois.edu) extractor for URLs. It will create a thumbnail
every website giving to it.

# Input format

It expects JSON input:
```json
{
    "url": "http://www.google.com"
}
```

# Metadata format

To Do

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

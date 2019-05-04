FROM python:3.4-alpine

ADD ./selenium /tests/selenium/
ADD entrypoint.sh /entrypoint.sh

RUN apk update && \
    apk add bash && \
    pip install selenium pytest pytest-html

ENTRYPOINT [ "bash", "-c", "/entrypoint.sh"]
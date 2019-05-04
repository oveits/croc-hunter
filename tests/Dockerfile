FROM python:3.4-alpine

RUN mkdir -p /selenium
ADD ./selenium /tests/selenium/
ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN apk update && \
    apk add bash && \
    pip install selenium pytest pytest-html

ENTRYPOINT ["/entrypoint.sh"]

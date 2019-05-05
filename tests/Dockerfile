FROM python:3.4-alpine

RUN mkdir -p /selenium
ADD ./selenium /tests/selenium/
ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN apk update && \
    apk add bash && \
    pip install selenium pytest pytest-html

ENTRYPOINT ["/entrypoint.sh"]

#CMD ["bash", "-c", "IFS=' ' read -a browserarray <<< '${{BROWSERS}}'' && for browser in '$${browserarray[@]}'; do BROWSER=$$browser python -m pytest -vvv --html=./${{CF_BUILD_ID}}-selenium-report-$${browser}.html --self-contained-html ./tests/selenium/test_app.py; done"]
CMD ["bash", "-c", "BROWSER=chrome SELENIUM_HUB_URL=http://dev-node1.vocon-it.com:30385/wd/hub INGRESS_HOSTNAME=crochunter.vocon-it.com python -m pytest -vvv --html=./selenium-report-chrome.html --self-contained-html ./tests/selenium/test_app.py"]
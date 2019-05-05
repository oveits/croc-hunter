#!/bin/bash

[ "$SELENIUM_HUB_URL" == "" ] && export SELENIUM_HUB_URL="http://selenium_hub:4444/wd/hub"
[ "$BROWSERS" == "" ] && export BROWSERS=chrome
[ "$BROWSER" == "" ] && export BROWSER=chrome
[ "$INGRESS_HOSTNAME" == "" ] && export INGRESS_HOSTNAME=crochunter.vocon-it.com


echo "SELENIUM_HUB_URL=$SELENIUM_HUB_URL"

echo "$@"
exec "$@"


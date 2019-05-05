#!/bin/bash

#[ "$SELENIUM_HUB_URL" == "" ] && export SELENIUM_HUB_URL="http://dev-node1.vocon-it.com:31881/wd/hub"
[ "$SELENIUM_HUB_URL" == "" ] && export SELENIUM_HUB_URL="http://selenium_hub:4444/wd/hub"
[ "$BROWSERS" == "" ] && export BROWSERS=chrome
#[ "$INGRESS_HOSTNAME" == "" ] && export INGRESS_HOSTNAME=crochunter.vocon-it.com
[ "$INGRESS_HOSTNAME" == "" ] && export INGRESS_HOSTNAME=localhost

echo "SELENIUM_HUB_URL=$SELENIUM_HUB_URL"

echo "$@"
exec "$@"


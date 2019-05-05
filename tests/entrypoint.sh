#!/bin/bash

[ "$SELENIUM_HUB_URL" == "" ] && export SELENIUM_HUB_URL="http://selenium_hub:4444/wd/hub"

echo "SELENIUM_HUB_URL=$SELENIUM_HUB_URL"

echo "$@"
exec "$@"


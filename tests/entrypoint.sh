
[ "$SELENIUM_HUB" == "" ] && export SELENIUM_HUB="http://selenium_hub:4444/wd/hub"

echo "$@"
exec "$@"
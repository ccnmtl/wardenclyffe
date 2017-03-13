APP=wardenclyffe
JS_FILES=media/js/dashboard.js media/js/help_windows.js
MAX_COMPLEXITY=5

all: jenkins

include *.mk

compose-migrate:
	docker-compose run web python manage.py migrate --settings=$(APP).settings_compose

compose-run:
	docker-compose up

compose-install: compose-migrate
	docker-compose run web python manage.py switch enable_s3 on --create --settings=$(APP).settings_compose
	docker-compose run web python manage.py flag allow_uploads --everyone --create --settings=$(APP).settings_compose

eslint: $(JS_SENTINAL)
	$(NODE_MODULES)/.bin/eslint $(JS_FILES)

.PHONY: eslint

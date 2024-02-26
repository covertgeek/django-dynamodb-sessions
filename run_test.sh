#!/usr/bin/env sh

# make sure there is not table before creating
python manage.py delete_session_table -f
# create dynamo session stable
python manage.py create_session_table

python manage.py test
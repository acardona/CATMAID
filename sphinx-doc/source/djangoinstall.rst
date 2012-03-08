Installation of the DJANGO backend
==================================

The Django backend is required to use the neuron catalogue and the
cropping tool.

Make sure that you have the following packages installed::

  sudo apt-get install python-virtualenv libpq-dev python-dev \
    libxml2-dev libxslt1-dev libjpeg-dev libtiff-dev

  sudo apt-get build-dep python-numpy python-h5py libgraphicsmagick++1-dev \
    libimage-exiftool-perl

You first need to create a Python virtualenv.  In this directory, run::

   virtualenv --no-site-packages env

Then run::

   source env/bin/activate

... to activate the virtualenv environment.  Then install the packages
at the right versions (the pip-frozen file is in the django subdirectory)::

   pip install -r pip-frozen

Here is the list of packages and version required::

   Django==1.3.1
   distribute==0.6.10
   django-devserver==0.3.1
   numpy==1.6.1
   h5py==2.0.1
   lxml==2.3.1
   phpserialize==1.2
   psycopg2==2.4.1
   sqlparse==0.1.3
   wsgiref==0.1.2
   pgmagick==0.5.1
   celery==2.4.6
   django-celery==2.4.2
   kombu==2.0.0
   django-kombu==0.9.4

*A note on the pgmagick module:* this is a wrapper for GraphicMagick (GM).
GM uses so-called delegates to support different file formats. Depending
of the presence of such a delegate a file format is supported or not. The
cropping tool uses GM through pgmagick and expects the libtiff and the
libjpeg delegates to be present. So make sure your GM installation
supports tiff (check e.g. with the help of "gm convert -list format").

If you want to be able to run the unit tests, you will need to allow
the catmaid database user (catmaid_user by default) to create new
databases.  You can do that with::

   postgres=# ALTER USER catmaid_user CREATEDB;
   ALTER ROLE

... and you should also add this line at the top of
*/etc/postgresql/8.4/main/pg_hba.conf* ::

    local test_catmaid catmaid_user md5

... and then restart PostgreSQL::

    /etc/init.d/postgresql-8.4 restart

Now copy settings.py.example to settings.py and edit it in the
following ways::

  * Set SECRET_KEY to a new value, as suggested in the comment.

  * Change the absolute path in TEMPLATE_DIRS to wherever the
    templates directory in this repository.

  * Change the STATICFILES_URL and STATICFILES_LOCAL variables to
    point to the right locations.

  * Change the absolute path in TMP_DIR to reflect space for
    temporary files (e.g. cropped stacks).  Make sure the web-server
    can read and write this folder.

  * Define CATMAID_DJANGO_URL te be the URL to your Django installation
    as seen from the outside.

Try running the server locally, with::

  ./manage.py runserver

... and visiting (you might have to be logged-in in your running CATMAID
instance::

  http://localhost:8000/[project_id]

If that works successfully, carry on to configure Apache.

Apache
------

First, install the wsgi Apache module::

   sudo apt-get install libapache2-mod-wsgi

Now copy *settings_apache.py*.example to settings_apache.py, and
customize that file.  Similarly, copy *django.wsgi.example* to
*django.wsgi* and customize that file.

Then you need to edit your Apache configuration to point to that WSGI
file and set up the appropriate aliases.  An example is given here::

    Alias /catmaid/dj-static/ /home/mark/catmaid-local-instance/django/static/

    Alias /catmaid/dj /home/mark/catmaid-local-instance/django/projects/mysite/django.wsgi
    <Location /catmaid/dj>
            SetHandler wsgi-script
            Options +ExecCGI
    </Location>

    Alias /catmaid/ /home/mark/catmaid-local-instance/httpdocs/

    <Directory /home/mark/catmaid-local-instance/httpdocs/>

            php_admin_value register_globals off
            php_admin_value include_path ".:/home/mark/catmaid-local-instance/inc"
            php_admin_value session.use_only_cookies 1
            php_admin_value error_reporting 2047
            php_admin_value display_errors true

            Options FollowSymLinks
            AllowOverride AuthConfig Limit FileInfo
            Order deny,allow
            Allow from all

    </Directory>

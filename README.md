# dun-dun-duh

Create dramatic, zoom in gifs!  This is what runs http://dun-dun-duh.com/.

# Running DDD

## What you need...

  * Python ~2.7
  * [gifsicle](http://www.lcdf.org/gifsicle/)
  * Redis

## Configuration

DDD does not have very many configuration options.  These can be placed in a python file with a path specified by a "CONFIG" environment variable.

### TIMEZONE

This is the timezone you want your statistics recorded in.  Since stats are driven by dates, you'll want to set this to your local timezone.

DDD expects the system to be configured to UTC time. If you don't, your statistics will be weird.

### SECRET_KEY

This is a Flask config variable, but necessary for DDD because we use sessions.

### REDIS_URL

This is a connection string in a manner that flask-and-redis can grok.

Defaults to <tt>redis://localhost:6379/0</tt>

### UPLOAD_DESTINATION

This determines whether completed gifs are stored on the local system, or S3.

Valid values are "s3" and "local".  Defaults to 'local'

### AWS\_ACCESS\_KEY / AWS\_SECRET\_KEY / S3_BUCKET

These are your AWS key and bucket name if you are storing gifs on S3.

### UPLOAD\_URL\_FORMAT_STRING

This is a brutal way to "fix" URL's for gifs.  It allows you to set a format string for a URL to a gif.

This value is "http://i.dun-dun-duh.com/%(filename)s" in production, because we have i.dun-dun-duh.com CNAME'd to the S3 bucket domain.

### UPLOAD_FOLDER

This is the path where we will store temporary upload files, and, if UPLOAD_DESTINATION is "local", output gifs.

Defaults to a folder named "upload" in the same directory as <tt>dundunduh/\_\_init\_\_.py</tt>

## Assets

Assets are in a half-broken state.  Sorry.

Right now, you need to rebuild them with Grunt when you change them.

## Execution

DDD runs in two parts.  The first is the web server component, the second is an RQ worker.

### Web Server

In development, you can run the web server through the built in debug server with manage.py

    $ CONFIG="/path/to/config.conf" manage.py runserver
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader
 
In production, you would want to use a different server.  For instance, gunicorn with nginx in front of it.  Here is an example supervisor config section.

    [program:app]
    environment=CONFIG="/opt/dundunduh/config.py"
    directory=/opt/dundunduh/source
    command=/opt/dundunduh/env/bin/gunicorn -w 4 -k gevent -b unix:/tmp/dundunduh.sock dundunduh:app
    user=app

### RQ Worker

The RQ worker is always run with manage.py

    $ CONFIG="/path/to/config.conf" manage.py work
    09:15:09 RQ worker started, version 0.3.11
    09:15:09 
    09:15:09 *** Listening on default...

In production, you should run several concurrently if you expect multiple jobs at once, and use the TERM signal to stop them gracefully.  Here is an example supervisor config section.

    [program:rq]
    environment=CONFIG="/opt/dundunduh/config.py"
    directory=/opt/dundunduh/source
    command=/opt/dundunduh/env/bin/python /opt/dundunduh/source/manage.py work
    process_name=%(program_name)s-%(process_num)s
    numprocs=4
    stopsignal=TERM
    user=app
    
    [group:workers]
    programs=rq

# License

Dun-Dun-Duh is licensed under MIT.

Have fun, work hard, be kind.

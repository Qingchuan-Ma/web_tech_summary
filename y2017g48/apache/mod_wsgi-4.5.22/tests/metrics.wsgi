from __future__ import print_function

import os
import sys
import locale

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

import mod_wsgi
import apache

def application(environ, start_response):
    print('request message #1', file=environ['wsgi.errors'])
    print('global message #1')
    print('queued message #1', end='')
    print('request message #2', file=environ['wsgi.errors'])
    print('global message #2')
    print('queued message #2', end='')
    print('request message #3', file=environ['wsgi.errors'])
    print('queued message #3', '+', sep="", end='')
    print('queued message #4', end='')

    headers = []
    headers.append(('Content-Type', 'text/plain; charset="UTF-8"'))
    write = start_response('200 OK', headers)

    input = environ['wsgi.input']
    output = StringIO()

    if os.name != 'nt':
        print('PID: %s' % os.getpid(), file=output)
        print('UID: %s' % os.getuid(), file=output)
        print('GID: %s' % os.getgid(), file=output)
        print('CWD: %s' % os.getcwd(), file=output)
        print(file=output)

    print('STDOUT:', sys.stdout.name, file=output)
    print('STDERR:', sys.stderr.name, file=output)
    print('ERRORS:', environ['wsgi.errors'].name, file=output)
    print(file=output)

    print('python.version: %r' % (sys.version,), file=output)
    print('python.prefix: %r' % (sys.prefix,), file=output)
    print('python.path: %r' % (sys.path,), file=output)
    print(file=output)

    print('apache.version: %r' % (apache.version,), file=output)
    print('mod_wsgi.version: %r' % (mod_wsgi.version,), file=output)
    print(file=output)

    print('mod_wsgi.process_group: %s' % mod_wsgi.process_group,
            file=output)
    print('mod_wsgi.application_group: %s' % mod_wsgi.application_group,
            file=output)
    print(file=output)

    print('mod_wsgi.maximum_processes: %s' % mod_wsgi.maximum_processes,
            file=output)
    print('mod_wsgi.threads_per_process: %s' % mod_wsgi.threads_per_process,
            file=output)
    print('mod_wsgi.process_metrics: %s' % mod_wsgi.process_metrics(),
            file=output)
    print('mod_wsgi.server_metrics: %s' % mod_wsgi.server_metrics(),
            file=output)
    print(file=output)

    metrics = mod_wsgi.server_metrics()

    if metrics:
        for process in metrics['processes']:
           for worker in process['workers']:
               print(worker['status'], file=output, end='')
        print(file=output)
        print(file=output)

    print('apache.description: %s' % apache.description, file=output)
    print('apache.build_date: %s' % apache.build_date, file=output)
    print('apache.mpm_name: %s' % apache.mpm_name, file=output)
    print('apache.maximum_processes: %s' % apache.maximum_processes,
            file=output)
    print('apache.threads_per_process: %s' % apache.threads_per_process,
            file=output)
    print(file=output)

    print('PATH: %s' % sys.path, file=output)
    print(file=output)

    print('LANG: %s' % os.environ.get('LANG'), file=output)
    print('LC_ALL: %s' % os.environ.get('LC_ALL'), file=output)
    print('sys.getdefaultencoding(): %s' % sys.getdefaultencoding(),
            file=output)
    print('sys.getfilesystemencoding(): %s' % sys.getfilesystemencoding(),
            file=output)
    print('locale.getlocale(): %s' % (locale.getlocale(),),
            file=output)
    print('locale.getdefaultlocale(): %s' % (locale.getdefaultlocale(),),
            file=output)
    print('locale.getpreferredencoding(): %s' % locale.getpreferredencoding(),
            file=output)
    print(file=output)

    keys = sorted(environ.keys())
    for key in keys:
        print('%s: %s' % (key, repr(environ[key])), file=output)
    print(file=output)

    keys = sorted(os.environ.keys())
    for key in keys:
        print('%s: %s' % (key, repr(os.environ[key])), file=output)
    print(file=output)

    result = output.getvalue()

    if not isinstance(result, bytes):
        result = result.encode('UTF-8')

    yield result

    block_size = 8192

    data = input.read(block_size)
    while data:
        yield data
        data = input.read(block_size)

import time
import threading
import os
import mod_wsgi

last_metrics = None

def monitor(*args):
    global last_metrics

    while True:
        current_metrics = mod_wsgi.process_metrics()

        if last_metrics is not None:
            cpu_user_time = (current_metrics['cpu_user_time'] -
                    last_metrics['cpu_user_time'])
            cpu_system_time = (current_metrics['cpu_system_time'] -
                    last_metrics['cpu_system_time'])

            request_busy_time = (current_metrics['request_busy_time'] -
                    last_metrics['request_busy_time'])

            request_threads = current_metrics['request_threads']

            # report data

            timestamp = int(current_metrics['current_time'] * 1000000000)

            item = {}
            item['time'] = timestamp
            item['measurement'] = 'process'
            item['process_group'] = mod_wsgi.process_group
            item['process_id'] = os.getpid()

            fields = {}

            fields['cpu_user_time'] = cpu_user_time
            fields['cpu_system_time'] = cpu_system_time

            fields['request_busy_time'] = request_busy_time
            fields['request_busy_usage'] = (request_busy_time /
                    mod_wsgi.threads_per_process)

            fields['threads_per_process'] = mod_wsgi.threads_per_process
            fields['request_threads'] = request_threads

            item['fields'] = fields

            print(item)

        last_metrics = current_metrics

        current_time = current_metrics['current_time']
        delay = max(0, (current_time + 1.0) - time.time())
        time.sleep(delay)

thread = threading.Thread(target=monitor)
thread.setDaemon(True)
thread.start()

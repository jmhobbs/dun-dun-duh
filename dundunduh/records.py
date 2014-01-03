# -*- coding: utf-8 -*-

import json
from datetime import datetime
from pytz import timezone

from flask import current_app
from .extensions import redis

rolling_average_lua = """
local i = redis.call('GET', KEYS[1])
local cai = redis.call('GET', KEYS[2])
i = tonumber(i)
cai = tonumber(cai)
if i == nil then
    i = 0
end
if cai == nil then
    cai = 0
end
cai = (tonumber(ARGV[1]) + (i * cai)) / (i + 1)
redis.call('SET', KEYS[2], cai)"""


def create_gif(slug, ip, queue_time, start_rendering, wait_duration, render_duration, store_duration, total_queue_duration):

    tz = timezone(current_app.config.get('TIMEZONE', 'UTC'))

    dt = datetime.fromtimestamp(queue_time)
    dt = tz.localize(dt)

    record = json.dumps({
        "slug": slug,
        "ip": ip,
        "timestamp": queue_time,
        "durations": {
            "wait": wait_duration,
            "render": render_duration,
            "store": store_duration,
            "total": total_queue_duration
        }
    })

    rolling_average_script = redis.connection.register_script(rolling_average_lua)

    pipe = redis.pipeline()

    pipe.lpush('gifs', record)

    pipe.incr('stats:created')
    pipe.incr('stats:created:%d-%02d-%02d' % (dt.year, dt.month, dt.day))
    pipe.incr('stats:created:%d-%02d-%02d %02d' % (dt.year, dt.month, dt.day, dt.hour))
    pipe.incr('stats:created:%d-%02d-%02d %02d:%02d' % (dt.year, dt.month, dt.day, dt.hour, (dt.minute / 5) * 5))

    rolling_average_script(keys=['stats:created', 'stats:average:total'], args=[total_queue_duration], client=pipe)
    rolling_average_script(keys=['stats:created', 'stats:average:wait'], args=[wait_duration], client=pipe)
    rolling_average_script(keys=['stats:created', 'stats:average:render'], args=[render_duration], client=pipe)
    rolling_average_script(keys=['stats:created', 'stats:average:store'], args=[store_duration], client=pipe)

    rolling_average_script(keys=['stats:created', 'stats:average:total:%d-%02d-%02d' % (dt.year, dt.month, dt.day)], args=[total_queue_duration], client=pipe)
    rolling_average_script(keys=['stats:created', 'stats:average:wait:%d-%02d-%02d' % (dt.year, dt.month, dt.day)], args=[wait_duration], client=pipe)
    rolling_average_script(keys=['stats:created', 'stats:average:render:%d-%02d-%02d' % (dt.year, dt.month, dt.day)], args=[render_duration], client=pipe)
    rolling_average_script(keys=['stats:created', 'stats:average:store:%d-%02d-%02d' % (dt.year, dt.month, dt.day)], args=[store_duration], client=pipe)

    rolling_average_script(keys=['stats:created', 'stats:average:total:%d-%02d-%02d %02d' % (dt.year, dt.month, dt.day, dt.hour)], args=[total_queue_duration], client=pipe)
    rolling_average_script(keys=['stats:created', 'stats:average:wait:%d-%02d-%02d %02d' % (dt.year, dt.month, dt.day, dt.hour)], args=[wait_duration], client=pipe)
    rolling_average_script(keys=['stats:created', 'stats:average:render:%d-%02d-%02d %02d' % (dt.year, dt.month, dt.day, dt.hour)], args=[render_duration], client=pipe)
    rolling_average_script(keys=['stats:created', 'stats:average:store:%d-%02d-%02d %02d' % (dt.year, dt.month, dt.day, dt.hour)], args=[store_duration], client=pipe)

    pipe.execute()


def create_gif_failed(queue_time):
    tz = timezone(current_app.config.get('TIMEZONE', 'UTC'))

    dt = datetime.fromtimestamp(queue_time)
    dt = tz.localize(dt)

    pipe = redis.pipeline()
    pipe.incr('stats:failed')
    pipe.incr('stats:failed:%d-%02d-%02d' % (dt.year, dt.month, dt.day))
    pipe.incr('stats:failed:%d-%02d-%02d %02d' % (dt.year, dt.month, dt.day, dt.hour))
    pipe.incr('stats:failed:%d-%02d-%02d %02d:%02d' % (dt.year, dt.month, dt.day, dt.hour, (dt.minute / 5) * 5))
    pipe.execute()


def get_daily_average(dt, type):
    avg = redis.get('stats:average:%s:%d-%02d-%02d' % (type, dt.year, dt.month, dt.day))
    if not avg:
        return 0
    return float(avg)


def get_hourly_average(dt, type):
    avg = redis.get('stats:average:%s:%d-%02d-%02d %02d' % (type, dt.year, dt.month, dt.day, dt.hour))
    if not avg:
        return 0
    return float(avg)

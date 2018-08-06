#!/usr/bin/env python
import pika
import sys

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='topics', exchange_type='topic')

routing_keys = sys.argv[1:]
if not routing_keys:
    sys.stderr.write("Usage: %s [routing_key]...\n" % sys.argv[0])
    sys.exit(1)

routing_key = routing_keys[0]

message = ' '.join(sys.argv[2:]) or ''
channel.basic_publish(exchange='topic_logs', routing_key=routing_key, body=message)
print(" [x] Sent %r:%r" % (routing_key, message))
connection.close()
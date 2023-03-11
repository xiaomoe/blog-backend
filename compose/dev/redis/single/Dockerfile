FROM redis:7-alpine

ENTRYPOINT [ "redis-server", "/redis.conf" ]
CMD [ "--requirepass", "${REDIS_PASSWORD}", "--masterauth", "${REDIS_PASSWORD}"]

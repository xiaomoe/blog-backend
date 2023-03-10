FROM redis:7-alpine

ENTRYPOINT ["redis-sentinel", "/sentinel.conf" ]

CMD ["--sentinel", "auth-pass", "redis", "${REDIS_PASSWORD}"]

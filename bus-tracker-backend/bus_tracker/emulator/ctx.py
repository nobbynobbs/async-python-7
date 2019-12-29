import contextvars

# It's absolutely unnecessary to use, I'd just been curios how it works,
# so I use ContextVar for access to worker_id in reconnect decorator
worker_index = contextvars.ContextVar("worker_index")

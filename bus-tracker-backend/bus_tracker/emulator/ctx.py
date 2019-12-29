from contextvars import ContextVar

# It's absolutely unnecessary to use, I'd just been curios how it works,
# so I use ContextVar for access to worker_id in reconnect decorator
worker_index: ContextVar[int] = ContextVar("worker_index")

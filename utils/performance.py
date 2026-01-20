"""Performance monitoring utilities."""
import time
import asyncio
from functools import wraps
from typing import Callable, Any
from simple_logger import logger


class PerformanceMonitor:
    """Monitor performance metrics for various operations."""

    def __init__(self):
        self.metrics = {}

    def record_latency(self, operation: str, latency: float):
        """Record latency for an operation."""
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'total_time': 0,
                'min': float('inf'),
                'max': 0,
                'recent': []
            }

        metric = self.metrics[operation]
        metric['count'] += 1
        metric['total_time'] += latency
        metric['min'] = min(metric['min'], latency)
        metric['max'] = max(metric['max'], latency)
        metric['recent'].append(latency)

        # Keep only last 100 measurements
        if len(metric['recent']) > 100:
            metric['recent'].pop(0)

    def get_stats(self, operation: str) -> dict:
        """Get statistics for an operation."""
        if operation not in self.metrics:
            return {}

        metric = self.metrics[operation]
        avg = metric['total_time'] / metric['count'] if metric['count'] > 0 else 0
        recent_avg = sum(metric['recent']) / len(metric['recent']) if metric['recent'] else 0

        return {
            'count': metric['count'],
            'avg': avg,
            'recent_avg': recent_avg,
            'min': metric['min'],
            'max': metric['max']
        }

    def log_stats(self):
        """Log performance statistics for all operations."""
        logger.info("=== Performance Statistics ===")
        for operation, stats in self.metrics.items():
            stat_info = self.get_stats(operation)
            logger.info(
                f"{operation}: "
                f"count={stat_info['count']}, "
                f"avg={stat_info['avg']:.3f}s, "
                f"recent_avg={stat_info['recent_avg']:.3f}s, "
                f"min={stat_info['min']:.3f}s, "
                f"max={stat_info['max']:.3f}s"
            )


# Global performance monitor instance
perf_monitor = PerformanceMonitor()


def measure_time(operation_name: str):
    """Decorator to measure execution time of synchronous functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                perf_monitor.record_latency(operation_name, elapsed)
                if elapsed > 1.0:  # Log if operation takes > 1 second
                    logger.warning(f"{operation_name} took {elapsed:.3f}s")
        return wrapper
    return decorator


def measure_time_async(operation_name: str):
    """Decorator to measure execution time of asynchronous functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                perf_monitor.record_latency(operation_name, elapsed)
                if elapsed > 1.0:  # Log if operation takes > 1 second
                    logger.warning(f"{operation_name} took {elapsed:.3f}s")
        return wrapper
    return decorator


class Timer:
    """Context manager for timing code blocks."""

    def __init__(self, operation_name: str, log_threshold: float = 1.0):
        self.operation_name = operation_name
        self.log_threshold = log_threshold
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        perf_monitor.record_latency(self.operation_name, self.elapsed)
        if self.elapsed > self.log_threshold:
            logger.warning(f"{self.operation_name} took {self.elapsed:.3f}s")

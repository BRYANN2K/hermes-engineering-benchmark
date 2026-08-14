def run_with_retry(operation, policy, sleep, retryable=(Exception,)):
    return operation()

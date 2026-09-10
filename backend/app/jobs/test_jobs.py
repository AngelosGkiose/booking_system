def say_hello():
    print("Hello from RQ worker")

def failing_job():
    raise Exception("Test failure")
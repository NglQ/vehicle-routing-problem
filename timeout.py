import signal
import time

stopped = {}


def get_running_instance():
    instance = []
    for key, value in stopped.items():
        if not value[0]:
            instance.append(key)
            start_time = value[1]
    assert len(instance) == 1, f'Instance list: {instance}'
    instance = instance[0]
    return instance, start_time


def timeout_handler():
    print(f'Handler: stopped = {stopped}')
    instance, _ = get_running_instance()

    i = 0
    while not stopped[instance][0]:
        i += 1
        print(f'Sending SIGINT to instance {instance} (attempt {i})...')
        signal.raise_signal(signal.SIGINT)
        time.sleep(1)
    print(f'Handler for instance {instance} finished.')


def check_timeout(time_limit: int):
    instance, start_time = get_running_instance()
    if time.time() - start_time >= time_limit:
        print(f'Timeout reached for instance {instance}.')
        stopped[instance] = (True, start_time)
        return True
    return False

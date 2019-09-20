import logging
import skein
import tensorflow as tf

from typing import Optional

from tf_yarn import (
    _task_commons,
    _internal,
    cluster,
    event,
    tensorboard
)


def main() -> None:
    task_type, task_id = cluster.get_task_description()
    task = cluster.get_task()
    client = skein.ApplicationClient.from_current()

    _task_commons._setup_container_logs(client)
    cluster_tasks = _task_commons._get_cluster_tasks(client)
    experiment = _task_commons._get_experiment(client)

    thread = _internal.MonitoredThread(
        name=f"{task_type}:{task_id}",
        target=tensorboard.start_tf_board,
        args=(client, experiment.estimator.config.model_dir),
        daemon=True)
    thread.start()

    for cluster_task in cluster_tasks:
        event.wait(client, f"{cluster_task}/stop")

    timeout = tensorboard.get_termination_timeout()
    thread.join(timeout)

    event.stop_event(client, task, thread.exception)
    event.broadcast_container_stop_time(client, task)


if __name__ == "__main__":
    _task_commons._process_arguments()
    main()

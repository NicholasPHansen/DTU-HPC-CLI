from enum import StrEnum

import typer

from dtu_hpc_cli.history import find_job


class Option(StrEnum):
    branch: str = "branch"
    commands: str = "commands"
    cores: str = "cores"
    feature: str = "feature"
    error: str = "error"
    gpus: str = "gpus"
    hosts: str = "hosts"
    memory: str = "memory"
    model: str = "model"
    name: str = "name"
    output: str = "output"
    queue: str = "queue"
    preamble: str = "preamble"
    split_every: str = "split_every"
    start_after: str = "start_after"
    sync: str = "sync"
    walltime: str = "walltime"


def execute_get_options(job_id: str, options: list[Option]):
    config = find_job(job_id)
    outputs = [get_option(config, option) for option in options]
    outputs = [output for output in outputs if output is not None]
    output = " ".join(outputs)
    typer.echo(output)


def get_option(config: dict, option: Option) -> str | None:
    key = option.value
    value = config[key]
    if value is None or (isinstance(value, list) and len(value) == 0):
        return None
    elif isinstance(value, list):
        return " ".join(f'--{key} "{v}"' for v in value)
    elif isinstance(value, bool):
        return f"--{key}" if value else f"no-{key}"
    else:
        return f"--{key} {value}"

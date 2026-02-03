import json
import time
from datetime import datetime
from pathlib import Path
from typing import List

import typer
from rich.progress import Console
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import Table
from rich.progress import TextColumn

from dtu_hpc_cli.client import get_client
from dtu_hpc_cli.config import DockerConfig
from dtu_hpc_cli.config import cli_config
from dtu_hpc_cli.error import error_and_exit
from dtu_hpc_cli.sync import check_and_confirm_changes
from dtu_hpc_cli.sync import execute_sync
from dtu_hpc_cli.types import Date

DOCKER_HISTORY_FILE = Path(".dtu_docker_history.json")


def load_history() -> list[dict]:
    path = DOCKER_HISTORY_FILE
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save_history(history: list[dict]):
    path = DOCKER_HISTORY_FILE
    path.write_text(json.dumps(history))


def add_to_history(config: DockerConfig, container_id: str, arguments: List[str]):
    history = load_history()

    _d = {
        "dockerfile": config.dockerfile,
        "gpus": config.gpus,
        "volumes": config.volumes,
        "imagename": config.imagename,
        "arguments": arguments,
    }
    history.append({"config": _d, "container_id": container_id, "timestamp": time.time()})
    save_history(history)


def show_docker_history(config: DockerConfig, arguments: List[str]):
    if not Path(DOCKER_HISTORY_FILE).exists():
        typer.echo(f"No history found in '{cli_config.history_path}'. You might not have submitted any jobs yet.")
        exit(0)

    history = load_history()

    table = Table(title="Docker Run Commands", show_lines=True)
    table.add_column("Timestamp")
    table.add_column("Container ID(s)")
    table.add_column("Dockerfile")
    table.add_column("GPU(s)")
    table.add_column("Volume(s)")
    table.add_column("Imagename")
    table.add_column("Commands")

    for entry in history:
        timestamp = datetime.fromtimestamp(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        container_id = entry["container_id"]

        _config = entry["config"]
        dockerfile = _config["dockerfile"]
        gpus = _config["gpus"] if _config["gpus"] else "-"
        volumes = "\n".join([f"{v['hostpath']}:{v['containerpath']}:{v['permissions']}" for v in _config["volumes"]])

        imagename = _config["imagename"]
        arguments = " ".join(_config["arguments"])

        row = [str(timestamp), container_id, dockerfile, gpus, volumes, imagename, arguments]

        # table.add_row([timestamp, container_id, dockerfile, gpus, volumes, imagename, arguments])
        table.add_row(*row)

    console = Console()
    console.print(table)


def run_docker_ps(config: DockerConfig, arguments: List[str]):
    with get_client() as client:
        cmd = "docker ps"
        returncode, stdout = client.run(cmd, cwd=cli_config.remote_path)


def run_docker_logs(config: DockerConfig, arguments: List[str]):
    cmd = ["journalctl", f"IMAGE_NAME={config.imagename}", "-o cat", "--all"]

    if len(arguments) == 0:
        # no arguments given, so just pull the logs for the latest run container
        history = load_history()
        container_id = history[-1]["container_id"]
        cmd.append(f"CONTAINER_ID={container_id}")

    else:
        if "a" in arguments:
            get_all_logs = True
            typer.echo("Pulling logs for all previously run containers...")

        if "n" in arguments:
            idx = arguments.index("n")
            get_n_logs = arguments[idx + 1]
            if not get_n_logs.isdigit():
                error_and_exit(f"Got unexpected argument for 'n': {get_n_logs}")
            cmd.append(f"-n {get_n_logs}")

        if "i" in arguments:
            idx = arguments.index("i")
            container_id = arguments[idx + 1]
            if len(container_id) != 12:
                error_and_exit(f"Expected 12 digit hash for argument for 'i', got: {container_id}")
            cmd.append(f"CONTAINER_ID={container_id}")

    cmd = " ".join(cmd)

    with get_client() as client:
        returncode, stdout = client.run(cmd, cwd=cli_config.remote_path)


def run_stop_docker_container(config: DockerConfig, arguments: List[str]):
    if len(arguments) == 0:
        history = load_history()
        container_id = history[-1]["container_id"]
    elif len(arguments[0]) == 12:
        # Provided a container_id
        container_id = arguments[0]
    else:
        error_and_exit("Argument is not a container id string")

    cmd = " ".join(["docker", "container", "stop", f"{container_id}"])
    with get_client() as client:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task(description="Stopping Container", total=None)
            progress.start()
            returncode, stdout = client.run(cmd, cwd=cli_config.remote_path)
            progress.update(task, completed=True)

    if returncode != 0:
        error_and_exit(f"Submission command failed with return code {returncode}.")


def run_docker_build(config: DockerConfig, arguments: List[str]):
    cmd = " ".join(["docker", "build", f"-f {config.dockerfile}", *arguments, f"-t {config.imagename}", "."])
    with get_client() as client:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task(description="Building Container", total=None)
            progress.start()
            returncode, stdout = client.run(cmd, cwd=cli_config.remote_path)
            progress.update(task, completed=True)

    if returncode != 0:
        error_and_exit(f"Submission command failed with return code {returncode}.")


def run_docker_container(config: DockerConfig, arguments: List[str]):
    run_docker_build(config, [])
    volumes = []
    if config.volumes is not None:
        volumes = [f"-v {v['hostpath']}:{v['containerpath']}:{v['permissions']}" for v in config.volumes]

    gpus = []
    if config.gpus is not None:
        gpus = [f"--gpus {config.gpus}"]

    cmd = " ".join(
        [
            "docker",
            "run",
            "--log-driver=journald",
            "--rm",
            "-d",
            # f"--name {config.imagename}",
            *volumes,
            *gpus,
            config.imagename,
            *arguments,
        ]
    )

    with get_client() as client:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task(description="Starting Container", total=None)
            progress.start()
            returncode, stdout = client.run(cmd, cwd=cli_config.remote_path)
            progress.update(task, completed=True)

    if returncode != 0:
        error_and_exit(f"Submission command failed with return code {returncode}.")

    # Grab the container id for history, only save the first 12 values of the hash
    container_id = stdout[:12]
    add_to_history(config, container_id, arguments)
    # typer.echo(stdout)


def execute_docker_command(config: DockerConfig, commands: List[str], sync: bool):
    docker_cmd = commands[0]
    arguments = commands[1:]

    docker_config = cli_config.docker
    valid_commands = {
        "stats": run_docker_ps,
        "logs": run_docker_logs,
        "history": show_docker_history,
        "stop": run_stop_docker_container,
        # "build": run_docker_build,
        "submit": run_docker_container,
    }

    if docker_cmd not in valid_commands:
        error_and_exit(f"Unknown command '{docker_cmd}'.")

    fn = valid_commands.get(docker_cmd)
    if (docker_cmd == "build" or docker_cmd == "submit") and sync:
        execute_sync(confirm_changes=True)

    fn(config, arguments)

    # if docker_cmd == "stats":
    #     run_docker_ps()
    #     return
    # elif docker_cmd == "logs":
    #     run_docker_logs(config, arguments)
    #     return
    # elif docker_cmd == "history":
    #     show_docker_history()
    #     return
    # elif docker_cmd == "stop":
    #     run_stop_docker_container(docker_config, arguments)
    #     return
    #
    # if sync:
    #     execute_sync(confirm_changes=True)
    #
    # if docker_cmd == "build":
    #     run_docker_build(docker_config, arguments)
    # elif docker_cmd == "submit":
    #     run_docker_container(docker_config, arguments)
    # else:
    #     error_and_exit(f"Unknown command '{docker_cmd}'.")

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

from dtu_hpc_cli import history
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


def show_docker_history():
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
        arguments = _config["arguments"]

        row = [str(timestamp), container_id, dockerfile, gpus, volumes, imagename, *arguments]

        # table.add_row([timestamp, container_id, dockerfile, gpus, volumes, imagename, arguments])
        table.add_row(*row)

    console = Console()
    console.print(table)


def execute_docker_command(config: DockerConfig, commands: List[str], sync: bool):
    docker_cmd = commands[0]
    arguments = commands[1:]

    if docker_cmd == "stats":
        run_docker_ps()
        return
    elif docker_cmd == "logs":
        run_docker_logs(config, arguments)
        return
    elif docker_cmd == "history":
        show_docker_history()
        return

    if sync:
        check_and_confirm_changes()
        execute_sync(confirm_changes=False)

    docker_config = cli_config.docker
    if docker_cmd == "build":
        run_docker_build(docker_config, arguments)
    elif docker_cmd == "submit":
        run_docker_container(docker_config, arguments)
    else:
        error_and_exit(f"Unknown command '{docker_cmd}'.")


def run_docker_ps():
    with get_client() as client:
        cmd = "docker ps"
        returncode, stdout = client.run(cmd, cwd=cli_config.remote_path)


def run_docker_logs(config: DockerConfig, arguments: List[str]):
    cmd = ["journalctl", f"CONTAINER_NAME={config.imagename}"]

    if len(arguments) == 0:
        # no arguments given, so just pull the logs for the latest run container
        history = load_history()
        container_id = history[-1]["container_id"]
        cmd.append(f"CONTAINER_ID={container_id}")

    else:
        if arguments[0] == "all":
            typer.echo("Pulling logs for all previously run containers...")

        elif len(arguments[0]) == 12:
            # Assumes a 12 digit hash is assumed provided
            container_id = arguments[0]
            cmd.append(f"CONTAINER_ID={container_id}")
        else:
            error_and_exit(f"Uknown arguemnt: {arguments}")

    cmd = " ".join(cmd)

    with get_client() as client:
        returncode, stdout = client.run(cmd, cwd=cli_config.remote_path)


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


#    typer.echo(stdout)


def run_docker_container(config: DockerConfig, arguments: List[str]):
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
            f"--name {config.imagename}",
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

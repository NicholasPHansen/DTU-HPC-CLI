from typing import List
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from dtu_hpc_cli.config import cli_config, DockerConfig
from dtu_hpc_cli.error import error_and_exit
from dtu_hpc_cli.client import get_client
from dtu_hpc_cli.sync import check_and_confirm_changes
from dtu_hpc_cli.sync import execute_sync


def execute_docker_command(config: DockerConfig, commands: List[str], sync: bool):
    docker_cmd = commands[0]
    arguments = commands[1:]

    if docker_cmd == "stats":
        run_docker_ps()
        return
    elif docker_cmd == "logs":
        run_docker_logs(config)
        return

    if sync:
        check_and_confirm_changes()
        execute_sync(confirm_changes=False)

    docker_config = cli_config.docker
    if docker_cmd == "build":
        run_docker_build(docker_config, arguments)
    elif docker_cmd == "run":
        run_docker_container(docker_config, arguments)
    else:
        error_and_exit(f"Unknown command '{docker_cmd}'.")


def run_docker_ps():
    with get_client() as client:
        cmd = "docker ps"
        returncode, stdout = client.run(cmd, cwd=cli_config.remote_path)


def run_docker_logs(config: DockerConfig):
    cmd = " ".join(["journalctl", f"CONTAINER_NAME={config.imagename}"])
    with get_client() as client:
        returncode, stdout = client.run(cmd, cwd=cli_config.remote_path)
    typer.echo(stdout)


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
    # typer.echo(stdout)


from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn

from dtu_hpc_cli.config import cli_config
from dtu_hpc_cli.error import error_and_exit
from dtu_hpc_cli.run import execute_run

def build_compose_file():
    docker = cli_config.docker
    arguments  = ["docker",  "compose", "-f", f"{docker.compose_file}",  "build"]

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(description="Building Container", total=None)
        progress.start()
        execute_run(arguments)
        progress.update(task, completed=True)


def run_docker_container(service: str = "trainer"):
    docker = cli_config.docker
    arguments = ["docker", "compose", "-f", f"{docker.compose_file}", "up", "-d" ]
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(description="Starting Container", total=None)
        progress.start()
        execute_run(arguments)
        progress.update(task, completed=True)

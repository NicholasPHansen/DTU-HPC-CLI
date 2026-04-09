from typing import List

import typer
from typing_extensions import Annotated

from dtu_hpc_cli.config import SubmitConfig
from dtu_hpc_cli.config import cli_config
from dtu_hpc_cli.constants import CONFIG_FILENAME
from dtu_hpc_cli.docker import DockerResubmitConfig
from dtu_hpc_cli.docker import execute_docker_build
from dtu_hpc_cli.docker import execute_docker_download
from dtu_hpc_cli.docker import execute_docker_history
from dtu_hpc_cli.docker import execute_docker_logs
from dtu_hpc_cli.docker import execute_docker_remove
from dtu_hpc_cli.docker import execute_docker_resubmit
from dtu_hpc_cli.docker import execute_docker_run
from dtu_hpc_cli.docker import execute_docker_stats
from dtu_hpc_cli.docker import execute_docker_stop
from dtu_hpc_cli.docker import execute_docker_submit
from dtu_hpc_cli.docker import execute_docker_volumes
from dtu_hpc_cli.download import execute_download
from dtu_hpc_cli.get_command import execute_get_command
from dtu_hpc_cli.get_options import Option
from dtu_hpc_cli.get_options import execute_get_options
from dtu_hpc_cli.history import HistoryConfig
from dtu_hpc_cli.history import execute_history
from dtu_hpc_cli.install import execute_install
from dtu_hpc_cli.jobs import JobsConfig
from dtu_hpc_cli.jobs import JobsStats
from dtu_hpc_cli.jobs import execute_jobs
from dtu_hpc_cli.open_error import execute_open_error
from dtu_hpc_cli.open_output import execute_open_output
from dtu_hpc_cli.queues import execute_queues
from dtu_hpc_cli.remove import RemoveConfig
from dtu_hpc_cli.remove import execute_remove
from dtu_hpc_cli.resubmit import ResubmitConfig
from dtu_hpc_cli.resubmit import execute_resubmit
from dtu_hpc_cli.run import execute_run
from dtu_hpc_cli.start_time import StartTimeConfig
from dtu_hpc_cli.start_time import execute_start_time
from dtu_hpc_cli.stats import StatsConfig
from dtu_hpc_cli.stats import execute_stats
from dtu_hpc_cli.submit import execute_submit
from dtu_hpc_cli.sync import execute_sync
from dtu_hpc_cli.types import Date
from dtu_hpc_cli.types import Duration
from dtu_hpc_cli.types import Memory
from dtu_hpc_cli.types import Time

__version__ = "1.5.0"

cli = typer.Typer(pretty_exceptions_show_locals=False)

docker_app = typer.Typer(help="Manage Docker containers on the remote (or local) machine.")
cli.add_typer(docker_app, name="docker")


class SubmitDefault:
    def __init__(self, key: str):
        self.key = key

    def __call__(self):
        return cli_config.submit.get(self.key)

    def __str__(self):
        value = cli_config.submit.get(self.key)
        return str(value)


class DockerDefault:
    def __init__(self, key: str):
        self.key = key

    def __call__(self):
        return getattr(cli_config.docker, self.key, None)

    def __str__(self):
        value = getattr(cli_config.docker, self.key, None)
        return str(value)


def profile_callback(profile: str | None):
    if profile is not None:
        cli_config.load_profile(profile)


def version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@cli.callback()
def main(
    profile: Annotated[
        str, typer.Option("--profile", callback=profile_callback, help="Optional profile from config.")
    ] = None,
    version: Annotated[bool, typer.Option("--version", callback=version_callback)] = False,
):
    pass


@cli.command()
def get_command(job_id: str):
    """Get the command used to submit a previous job."""
    execute_get_command(job_id)


@cli.command()
def get_options(job_id: str, options: List[Option]):
    """Print options from a previously submitted job."""
    execute_get_options(job_id, options)


@cli.command()
def history(
    branch: bool = True,
    branch_contains: str | None = None,
    branch_is: str | None = None,
    commands: bool = True,
    command_contains: str | None = None,
    command_is: str | None = None,
    confirm: bool = False,
    cores: bool = True,
    cores_above: int | None = None,
    cores_below: int | None = None,
    cores_is: int | None = None,
    date: bool = True,
    date_after: Annotated[Date, typer.Option(parser=Date.parse)] = None,
    date_before: Annotated[Date, typer.Option(parser=Date.parse)] = None,
    date_is: Annotated[Date, typer.Option(parser=Date.parse)] = None,
    feature: bool = False,
    feature_contains: str | None = None,
    feature_is: str | None = None,
    error: bool = False,
    error_contains: str | None = None,
    error_is: str | None = None,
    gpus: bool = True,
    gpus_above: int | None = None,
    gpus_below: int | None = None,
    gpus_is: int | None = None,
    hosts: bool = False,
    hosts_above: int | None = None,
    hosts_below: int | None = None,
    hosts_is: int | None = None,
    limit: int = 5,
    memory: bool = True,
    memory_above: Annotated[Memory, typer.Option(parser=Memory.parse)] = None,
    memory_below: Annotated[Memory, typer.Option(parser=Memory.parse)] = None,
    memory_is: Annotated[Memory, typer.Option(parser=Memory.parse)] = None,
    model: bool = False,
    model_contains: str | None = None,
    model_is: str | None = None,
    name: bool = True,
    name_contains: str | None = None,
    name_is: str | None = None,
    output: bool = False,
    output_contains: str | None = None,
    output_is: str | None = None,
    queue: bool = True,
    queue_contains: str | None = None,
    queue_is: str | None = None,
    preamble: bool = False,
    preamble_contains: str | None = None,
    preamble_is: str | None = None,
    split_every: bool = False,
    split_every_above: Annotated[Duration, typer.Option(parser=Duration.parse)] = None,
    split_every_below: Annotated[Duration, typer.Option(parser=Duration.parse)] = None,
    split_every_is: Annotated[Duration, typer.Option(parser=Duration.parse)] = None,
    start_after: bool = False,
    start_after_contains: str | None = None,
    start_after_is: str | None = None,
    sync: bool = False,
    time: bool = True,
    time_after: Annotated[Time, typer.Option(parser=Time.parse)] = None,
    time_before: Annotated[Time, typer.Option(parser=Time.parse)] = None,
    time_is: Annotated[Time, typer.Option(parser=Time.parse)] = None,
    walltime: bool = True,
    walltime_above: Annotated[Duration, typer.Option(parser=Duration.parse)] = None,
    walltime_below: Annotated[Duration, typer.Option(parser=Duration.parse)] = None,
    walltime_is: Annotated[Duration, typer.Option(parser=Duration.parse)] = None,
):
    """Show the history of submitted jobs."""
    config = HistoryConfig(
        branch=branch,
        branch_contains=branch_contains,
        branch_is=branch_is,
        commands=commands,
        command_contains=command_contains,
        command_is=command_is,
        confirm=confirm,
        cores=cores,
        cores_above=cores_above,
        cores_below=cores_below,
        cores_is=cores_is,
        date=date,
        date_after=date_after,
        date_before=date_before,
        date_is=date_is,
        feature=feature,
        feature_contains=feature_contains,
        feature_is=feature_is,
        error=error,
        error_contains=error_contains,
        error_is=error_is,
        gpus=gpus,
        gpus_above=gpus_above,
        gpus_below=gpus_below,
        gpus_is=gpus_is,
        hosts=hosts,
        hosts_above=hosts_above,
        hosts_below=hosts_below,
        hosts_is=hosts_is,
        limit=limit,
        memory=memory,
        memory_above=memory_above,
        memory_below=memory_below,
        memory_is=memory_is,
        model=model,
        model_contains=model_contains,
        model_is=model_is,
        name=name,
        name_contains=name_contains,
        name_is=name_is,
        output=output,
        output_contains=output_contains,
        output_is=output_is,
        queue=queue,
        queue_contains=queue_contains,
        queue_is=queue_is,
        preamble=preamble,
        preamble_contains=preamble_contains,
        preamble_is=preamble_is,
        split_every=split_every,
        split_every_above=split_every_above,
        split_every_below=split_every_below,
        split_every_is=split_every_is,
        start_after=start_after,
        start_after_contains=start_after_contains,
        start_after_is=start_after_is,
        sync=sync,
        time=time,
        time_after=time_after,
        time_before=time_before,
        time_is=time_is,
        walltime=walltime,
        walltime_above=walltime_above,
        walltime_below=walltime_below,
        walltime_is=walltime_is,
    )
    execute_history(config)


@cli.command()
def install():
    """Run the install script in the remote directory on the HPC."""
    execute_install()


@cli.command()
def jobs(
    node: str | None = None,
    queue: str | None = None,
    stats: Annotated[JobsStats, typer.Option()] = None,
):
    """List running and pending jobs."""
    list_config = JobsConfig(node=node, queue=queue, stats=stats)
    execute_jobs(list_config)


@cli.command()
def open_error(job_id: str):
    """Show the job error in your editor."""
    execute_open_error(job_id)


@cli.command()
def open_output(job_id: str):
    """Show the job output in your editor."""
    execute_open_output(job_id)


@cli.command()
def queues(queue: Annotated[str, typer.Argument()] = None):
    """List available queues."""
    execute_queues(queue)


@cli.command()
def remove(job_ids: List[str], from_history: bool = False):
    """Remove jobs from the queue."""
    config = RemoveConfig(from_history=from_history, job_ids=job_ids)
    execute_remove(config)


@cli.command()
def resubmit(
    job_id: str,
    branch: str = None,
    command: List[str] = None,
    confirm: bool = None,
    cores: int = None,
    email: str = None,
    error: str = None,
    feature: List[str] = None,
    gpus: int = None,
    hosts: int = None,
    memory: Annotated[Memory, typer.Option(parser=Memory.parse)] = None,
    model: str = None,
    name: str = None,
    notify_begin: bool = None,
    notify_end: bool = None,
    notify_fail: bool = None,
    output: str = None,
    preamble: List[str] = None,
    queue: str = None,
    split_every: Annotated[Duration, typer.Option(parser=Duration.parse)] = None,
    start_after: str = None,
    sync: bool = None,
    walltime: Annotated[Duration, typer.Option(parser=Duration.parse)] = None,
):
    """Resubmit a job. Optionally with new parameters."""
    config = ResubmitConfig(
        job_id=job_id,
        branch=branch,
        commands=command,
        confirm=confirm,
        cores=cores,
        email=email,
        error=error,
        feature=feature,
        gpus=gpus,
        hosts=hosts,
        memory=memory,
        model=model,
        name=name,
        notify_begin=notify_begin,
        notify_end=notify_end,
        notify_fail=notify_fail,
        output=output,
        preamble=preamble,
        queue=queue,
        split_every=split_every,
        start_after=start_after,
        sync=sync,
        walltime=walltime,
    )
    execute_resubmit(config)


@cli.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run(ctx: typer.Context):
    """Run a command on the HPC.

    Uses the configured remote path as the working directory."""
    execute_run(ctx.args)


@cli.command()
def start_time(job_ids: Annotated[List[str], typer.Argument()] = None, queue: str = None, user: str = None):
    """Show the start time of pending jobs."""
    config = StartTimeConfig(job_ids=job_ids, queue=queue, user=user)
    execute_start_time(config)


@cli.command()
def stats(
    queue: Annotated[str, typer.Argument()] = None,
    cpu: bool = False,
    gpu: bool = False,
    jobs: bool = False,
    memory: bool = False,
    node: str | None = None,
    reserved: bool = False,
):
    """Show statistics for the queue(s)."""
    config = StatsConfig(
        cpu=cpu,
        gpu=gpu,
        jobs=jobs,
        memory=memory,
        node=node,
        reserved=reserved,
        queue=queue,
    )
    execute_stats(config)


@cli.command()
def submit(
    commands: List[str],
    branch: Annotated[str, typer.Option(default_factory=SubmitDefault("branch"))],
    cores: Annotated[int, typer.Option(default_factory=SubmitDefault("cores"))],
    confirm: Annotated[bool, typer.Option(default_factory=SubmitDefault("confirm"))],
    email: Annotated[str, typer.Option(default_factory=SubmitDefault("email"))],
    error: Annotated[str, typer.Option(default_factory=SubmitDefault("error"))],
    feature: Annotated[List[str], typer.Option(default_factory=SubmitDefault("feature"))],
    gpus: Annotated[int, typer.Option(default_factory=SubmitDefault("gpus"))],
    hosts: Annotated[int, typer.Option(default_factory=SubmitDefault("hosts"))],
    memory: Annotated[Memory, typer.Option(parser=Memory.parse, default_factory=SubmitDefault("memory"))],
    model: Annotated[str, typer.Option(default_factory=SubmitDefault("model"))],
    name: Annotated[str, typer.Option(default_factory=SubmitDefault("name"))],
    notify_begin: Annotated[bool, typer.Option(default_factory=SubmitDefault("notify_begin"))],
    notify_end: Annotated[bool, typer.Option(default_factory=SubmitDefault("notify_end"))],
    notify_fail: Annotated[bool, typer.Option(default_factory=SubmitDefault("notify_fail"))],
    output: Annotated[str, typer.Option(default_factory=SubmitDefault("output"))],
    preamble: Annotated[List[str], typer.Option(default_factory=SubmitDefault("preamble"))],
    queue: Annotated[str, typer.Option(default_factory=SubmitDefault("queue"))],
    split_every: Annotated[Duration, typer.Option(parser=Duration.parse, default_factory=SubmitDefault("split_every"))],
    start_after: Annotated[str, typer.Option(default_factory=SubmitDefault("start_after"))],
    sync: Annotated[bool, typer.Option(default_factory=SubmitDefault("sync"))],
    walltime: Annotated[Duration, typer.Option(parser=Duration.parse, default_factory=SubmitDefault("walltime"))],
):
    """Submit a job to the queue."""
    submit_config = SubmitConfig(
        branch=branch,
        commands=commands,
        confirm=confirm,
        cores=cores,
        email=email,
        error=error,
        feature=feature,
        gpus=gpus,
        hosts=hosts,
        memory=memory,
        model=model,
        name=name,
        notify_begin=notify_begin,
        notify_end=notify_end,
        notify_fail=notify_fail,
        output=output,
        preamble=preamble,
        queue=queue,
        split_every=split_every,
        start_after=start_after,
        sync=sync,
        walltime=walltime,
    )
    execute_submit(submit_config)


@docker_app.callback()
def docker_callback():
    cli_config.check_docker(msg=f"docker requires a Docker configuration in '{CONFIG_FILENAME}'")


@docker_app.command("submit")
def docker_submit(
    commands: List[str],
    dockerfile: Annotated[str, typer.Option(default_factory=DockerDefault("dockerfile"))],
    imagename: Annotated[str, typer.Option(default_factory=DockerDefault("imagename"))],
    gpus: Annotated[str, typer.Option(default_factory=DockerDefault("gpus"))],
    sync: Annotated[bool, typer.Option(default_factory=DockerDefault("sync"))],
):
    """Build the image and run a container with the given command(s)."""
    execute_docker_submit(cli_config.docker, commands, sync=sync, dockerfile=dockerfile, imagename=imagename, gpus=gpus)


@docker_app.command("run")
def docker_run(
    commands: List[str],
    imagename: Annotated[str, typer.Option(default_factory=DockerDefault("imagename"))],
    gpus: Annotated[str, typer.Option(default_factory=DockerDefault("gpus"))],
):
    """Run a container from an already-built image."""
    execute_docker_run(cli_config.docker, commands, imagename=imagename, gpus=gpus)


@docker_app.command("install")
def docker_install(
    dockerfile: Annotated[str, typer.Option(default_factory=DockerDefault("dockerfile"))],
    imagename: Annotated[str, typer.Option(default_factory=DockerDefault("imagename"))],
    sync: Annotated[bool, typer.Option(default_factory=DockerDefault("sync"))],
):
    """Install (build) the Docker image."""
    execute_docker_build(cli_config.docker, sync=sync, dockerfile=dockerfile, imagename=imagename)


@docker_app.command("logs")
def docker_logs(
    imagename: Annotated[str, typer.Option(default_factory=DockerDefault("imagename"))],
    container_id: str | None = None,
    all: bool = False,
    n: int | None = None,
):
    """Show logs from a container (defaults to last run container)."""
    execute_docker_logs(cli_config.docker, container_id=container_id, imagename=imagename, all=all, n=n)


@docker_app.command("stop")
def docker_stop(container_id: str | None = None):
    """Stop a running container (defaults to last run container)."""
    execute_docker_stop(cli_config.docker, container_id=container_id)


@docker_app.command("jobs")
def docker_jobs():
    """List running containers (docker ps)."""
    execute_docker_stats(cli_config.docker)


@docker_app.command("history")
def docker_history():
    """Show history of past Docker runs."""
    execute_docker_history(cli_config.docker)


@docker_app.command("volumes")
def docker_volumes():
    """List files in docker-mounted volumes using workdir-relative paths."""
    execute_docker_volumes(cli_config.docker)


@docker_app.command("download")
def docker_download(
    path: Annotated[
        str | None,
        typer.Argument(help="Workdir-relative path to download (as shown by docker volumes)"),
    ] = None,
    local_path: Annotated[
        str | None,
        typer.Option("--local-path", "-l", help="Local destination path (defaults to project root)"),
    ] = None,
    list_only: Annotated[
        bool,
        typer.Option("--list", help="List files in docker-mounted volumes (same as docker volumes)"),
    ] = False,
):
    """Download a file from a docker volume by its workdir-relative path.

    Files are downloaded preserving their directory structure relative to project root."""
    if list_only:
        execute_docker_volumes(cli_config.docker)
        return
    if path is None:
        typer.echo("Error: Missing argument 'PATH'. Use --list to see available files.")
        raise typer.Exit(1)
    execute_docker_download(cli_config.docker, path=path, local_path=local_path)


@docker_app.command("resubmit")
def docker_resubmit(
    container_id: str | None = None,
    commands: List[str] | None = None,
    dockerfile: str | None = None,
    imagename: str | None = None,
    gpus: str | None = None,
):
    """Resubmit a previous Docker run (defaults to latest). Optionally with new parameters."""
    config = DockerResubmitConfig(
        container_id=container_id,
        commands=commands,
        dockerfile=dockerfile,
        imagename=imagename,
        gpus=gpus,
    )
    execute_docker_resubmit(cli_config.docker, config)


@docker_app.command("remove")
def docker_remove(
    container_ids: Annotated[List[str], typer.Argument()] = None,
    from_history: bool = False,
):
    """Remove container(s) (defaults to last run container). Optionally remove from history."""
    execute_docker_remove(cli_config.docker, container_ids=container_ids, from_history=from_history)


@cli.command()
def sync():
    """Sync the local directory with the remote directory on the HPC."""
    cli_config.check_ssh(msg=f"Sync requires a SSH configuration in '{CONFIG_FILENAME}'.")
    execute_sync()


@cli.command()
def download(
    remote_path: Annotated[
        str | None,
        typer.Option(
            "--remote-path",
            "-r",
            help="Sub-path within remote directory to download",
        ),
    ] = None,
    local_path: Annotated[
        str | None,
        typer.Option("--local-path", "-l", help="Local destination path (defaults to project root)"),
    ] = None,
    list_only: Annotated[
        bool,
        typer.Option("--list", help="Preview files without transferring (dry-run)"),
    ] = False,
    all_files: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Download all files, including those in .gitignore (ignores .gitignore)",
        ),
    ] = False,
):
    """Download files from the remote HPC directory to local.

    By default, files matching .gitignore patterns are excluded.
    Use --all to download all files regardless of .gitignore.
    Files are downloaded preserving their directory structure (relative to project root)."""
    cli_config.check_ssh(msg=f"Download requires a SSH configuration in '{CONFIG_FILENAME}'.")
    execute_download(
        remote_subpath=remote_path,
        local_path=local_path,
        list_only=list_only,
        all_files=all_files,
    )


if __name__ == "__main__":
    cli()

import subprocess

from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn

from dtu_hpc_cli.config import cli_config
from dtu_hpc_cli.error import error_and_exit


def execute_download(
    remote_subpath: str | None = None,
    local_path: str | None = None,
    list_only: bool = False,
    all_files: bool = False,
):
    ssh = cli_config.ssh
    base = cli_config.remote_path
    source = f"{base}/{remote_subpath}" if remote_subpath else base
    destination = f"{ssh.user}@{ssh.hostname}:{source}"

    if local_path is None:
        local_path = str(cli_config.project_root)

    command = [
        "rsync",
        "-avz",
        "-e",
        f"ssh -i {ssh.identityfile}",
        "--exclude=.git",
    ]

    if list_only:
        command.append("--dry-run")
    if all_files:
        command.append("--ignore-times")
    else:
        command.append("--exclude-from=.gitignore")

    # When downloading a subpath, use --relative to preserve directory structure
    if remote_subpath:
        command.append("--relative")
        # Mark the beginning of the relative path with ./
        source_with_marker = f"{base}/./{ remote_subpath}"
        destination = f"{ssh.user}@{ssh.hostname}:{source_with_marker}"

    command.extend([
        f"{destination}/",
        f"{local_path}/",
    ])

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(description="Downloading", total=None)
        progress.start()
        try:
            result = subprocess.run(command, check=True, capture_output=True)
            if list_only:
                # Print the dry-run output showing which files would be transferred
                stdout = result.stdout.decode()
                if stdout:
                    print(stdout)
        except subprocess.CalledProcessError as e:
            error_and_exit(f"Download failed:\n{e.stderr.decode()}")
        progress.update(task, completed=True)

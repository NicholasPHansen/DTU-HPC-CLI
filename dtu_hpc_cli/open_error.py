from dtu_hpc_cli import editor
from dtu_hpc_cli.client import get_client
from dtu_hpc_cli.error import error_and_exit
from dtu_hpc_cli.history import find_job


def execute_open_error(job_id: str):
    config = find_job(job_id)
    path = f"{config['output']}/{config['name']}_{job_id}.err"
    client = get_client()
    if not client.exists(path):
        error_and_exit(f"Error log file '{path}' does not exist.")
    contents = client.load(path)
    client.close()
    editor.open(text=contents)

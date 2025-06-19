from dtu_hpc_cli import editor
from dtu_hpc_cli.client import get_client
from dtu_hpc_cli.error import error_and_exit
from dtu_hpc_cli.history import find_job


def execute_open_output(job_id: str):
    config = find_job(job_id)
    path = f"{config['output']}/{config['name']}_{job_id}.out"
    client = get_client()
    if not client.exists(path):
        error_and_exit(f"Log file '{path}' does not exist.")
    contents = client.load(path)
    client.close()
    editor.open(text=contents)

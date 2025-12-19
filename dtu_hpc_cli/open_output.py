from dtu_hpc_cli import editor
from dtu_hpc_cli.client import get_client
from dtu_hpc_cli.error import error_and_exit
from dtu_hpc_cli.history import find_job_and_sub_id
from dtu_hpc_cli.types import Duration


def execute_open_output(job_id: str):
    config, sub_id = find_job_and_sub_id(job_id)
    walltime = Duration.parse(config["walltime"])
    split_every = Duration.parse(config["split_every"])
    if walltime > split_every:
        path = f"{config['output']}/{config['name']}-{sub_id}_{job_id}.out"
    else:
        path = f"{config['output']}/{config['name']}_{job_id}.out"
    client = get_client()
    if not client.exists(path):
        error_and_exit(f"Output log file '{path}' does not exist.")
    contents = client.load(path)
    client.close()
    editor.open(text=contents)

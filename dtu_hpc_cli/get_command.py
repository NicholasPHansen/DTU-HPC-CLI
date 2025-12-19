import typer

from dtu_hpc_cli.history import find_job

# These are automatically added fields that are not part of the submit command
INVALID_FIELDS = {"date", "time"}


def execute_get_command(job_id: str):
    config = find_job(job_id)

    preamble = config.pop("preamble", [])
    submit_commands = config.pop("commands", [])

    keys = sorted(set(config.keys()) - INVALID_FIELDS)

    command = ["dtu submit"]
    for key in keys:
        value = config[key]
        if value is None or (isinstance(value, list) and len(value) == 0):
            continue
        key = key.replace("_", "-")
        if isinstance(value, bool):
            if value:
                command.append(f"--{key}")
            else:
                command.append(f"--no-{key}")
        elif isinstance(value, list):
            for v in value:
                command.append(f"--{key} {v}")
        else:
            command.append(f"--{key} {value}")

    command.extend(f'--preamble "{c}"' for c in preamble)
    command.extend(f'"{c}"' for c in submit_commands)
    command = " \\\n    ".join(command)

    typer.echo(command)

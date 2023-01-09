from os.path import exists, join
import shlex
import subprocess
from re import search as regex_search
from typing import Union

from ocrd_webapi.constants import (
    DEFAULT_INPUT_GROUP,
    DEFAULT_METS_NAME,
    DEFAULT_NF_REPORT_NAME
)


# Must be further refined
class NextflowManager:
    def __init__(self):
        pass

    @staticmethod
    def execute_workflow(
            nf_script_path: str,
            workspace_path: str,
            job_dir: str,
            workflow_params: dict
    ):
        # Gets the values from the dictionary, if missing assign defaults
        if workflow_params:
            workspace_mets = workflow_params.get('mets', DEFAULT_METS_NAME)
            input_group = workflow_params.get('input_group', DEFAULT_INPUT_GROUP)
        else:
            workspace_mets = DEFAULT_METS_NAME
            input_group = DEFAULT_INPUT_GROUP

        # TODO: Parse the rest of the possible workflow params
        # TODO: Use workflow_params to enable more flexible workflows
        nf_command = NextflowManager.build_nf_command(
            nf_script_path=nf_script_path,
            ws_path=workspace_path,
            ws_mets=workspace_mets,
            input_group=input_group
        )

        # Throws an exception if not successful
        NextflowManager.__start_nf_process(nf_command, job_dir)

    @staticmethod
    def is_nf_available() -> Union[str, None]:
        # The path to Nextflow must be in $PATH
        # Otherwise, the full path must be provided

        # TODO: May be a good idea to define
        # the path to Nextflow somewhere else
        # (as a config or const parameter)
        ver_cmd = "nextflow -v"

        try:
            # Raises an exception if the subprocess fails
            ver_process = subprocess.run(shlex.split(ver_cmd),
                                         shell=False,
                                         check=True,
                                         stdout=subprocess.PIPE,
                                         universal_newlines=True)
        # Only the result is important not why it failed
        except Exception:
            return None

        regex_pattern = r"nextflow version\s*([\d.]+)"
        nf_version = regex_search(regex_pattern, ver_process.stdout).group(1)
        return nf_version

    @staticmethod
    def build_nf_command(nf_script_path: str, ws_path: str, ws_mets: str, input_group: str) -> str:
        nf_command = "nextflow -bg"
        nf_command += f" run {nf_script_path}"
        nf_command += f" --workspace {ws_path}/"
        nf_command += f" --mets {ws_path}/{ws_mets}"
        nf_command += f" --input_group {input_group}"
        nf_command += f" -with-report {DEFAULT_NF_REPORT_NAME}"
        return nf_command

    @staticmethod
    def __start_nf_process(nf_command: str, job_dir: str):
        nf_out = f'{job_dir}/nextflow_out.txt'
        nf_err = f'{job_dir}/nextflow_err.txt'

        # TODO: Not sure if this is too much to be handled in a single
        #  try catch block structure.
        try:
            with open(nf_out, 'w+') as nf_out_file:
                with open(nf_err, 'w+') as nf_err_file:
                    # TODO: Maybe we need a better management here,
                    #  For example knowing the PID of the created sub process
                    #  should help for better error/recovery management
                    # Raises an exception if the subprocess fails
                    subprocess.run(shlex.split(nf_command),
                                   shell=False,
                                   check=True,
                                   cwd=job_dir,
                                   stdout=nf_out_file,
                                   stderr=nf_err_file,
                                   universal_newlines=True)
        # More detailed exception catches needed
        # E.g., was the exception due to IOError or subprocess.CalledProcessError
        except Exception as error:
            raise error

    @staticmethod
    def is_nf_report(location_dir: str, report_name: str = None) -> Union[str, None]:
        if report_name is None:
            report_name = DEFAULT_NF_REPORT_NAME
        report_path = join(location_dir, report_name)
        if exists(report_path):
            return report_path
        return None

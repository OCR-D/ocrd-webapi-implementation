from os.path import exists, join
import shlex
import subprocess
from re import search as regex_search
from typing import Union

from ocrd_utils import getLogger


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
    ) -> Union[bool, Exception]:

        # Gets the values from the dictionary, if missing assign defaults
        if workflow_params:
            workspace_mets = workflow_params.get('mets', 'mets.xml')
            input_group = workflow_params.get('input_group', 'OCR-D-IMG')
        else:
            workspace_mets = 'mets.xml'
            input_group = 'input_group'

        # TODO: Parse the rest of the possible workflow params
        # TODO: Use workflow_params to enable more flexible workflows
        nf_command = NextflowManager.build_nf_command(
            nf_script_path=nf_script_path,
            workspace_path=workspace_path,
            workspace_mets=workspace_mets,
            input_group=input_group
        )
        try:
            return NextflowManager.start_nf_process(nf_command, job_dir)
        except Exception as error:
            getLogger(__name__).log.exception(f"Failed to execute workflow: {error}")
            raise error

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
        except Exception as error:
            getLogger(__name__).log.error(f"Failed to detect Nextflow installation, {error}")
            return None

        nf_version = NextflowManager.__parse_nf_version(ver_process.stdout)
        if nf_version:
            getLogger(__name__).log.info(f"Installed Nextflow version: {nf_version}")
        else:
            getLogger(__name__).log.error(f"Installed Nextflow version: None")
        return nf_version

    @staticmethod
    def __parse_nf_version(version_string: str) -> Union[str, None]:
        regex_pattern = r"nextflow version\s*([\d.]+)"
        nf_version = regex_search(regex_pattern, version_string).group(1)
        return nf_version

    @staticmethod
    def build_nf_command(
            nf_script_path: str,
            workspace_path: str,
            workspace_mets: str,
            input_group: str
    ) -> str:
        nf_command = "nextflow -bg"
        nf_command += f" run {nf_script_path}"
        nf_command += f" --workspace {workspace_path}/"
        nf_command += f" --mets {workspace_path}/{workspace_mets}"
        nf_command += f" --input_group {input_group}"
        nf_command += " -with-report"
        return nf_command

    @staticmethod
    def start_nf_process(nf_command: str, job_dir: str) -> Union[bool, Exception]:
        # Must be refined
        nf_out = f'{job_dir}/nextflow_out.txt'
        nf_err = f'{job_dir}/nextflow_err.txt'

        # TODO: Not sure if this is too much to be handled in a single
        #  try catch block structure.
        try:
            with open(nf_out, 'w+') as nf_out_file:
                with open(nf_err, 'w+') as nf_err_file:
                    # Raises an exception if the subprocess fails
                    nf_process = subprocess.run(shlex.split(nf_command),
                                                shell=False,
                                                check=True,
                                                cwd=job_dir,
                                                stdout=nf_out_file,
                                                stderr=nf_err_file,
                                                universal_newlines=True)
        # More detailed exception catches needed
        # E.g., was the exception due to IOError or subprocess.CalledProcessError
        except Exception as error:
            getLogger(__name__).log.exception(f"Nextflow process failed to start: {error}")
        return True

    @staticmethod
    def is_nf_report(location_dir: str, report_name: str = None) -> Union[str, None]:
        if report_name is None:
            report_name = "report.html"
        report_path = join(location_dir, report_name)
        if exists(report_path):
            return report_path
        return None

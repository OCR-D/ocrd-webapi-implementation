import shlex
import subprocess
from re import search as regex_search

from ocrd_utils import getLogger


# Must be further refined
class NextflowExecutor:
    def __init__(self):
        # Check if Nextflow is installed
        # If installed, get the version
        self.log = getLogger('ocrd_webapi.nextflow_executor')
        self.nf_version = self.is_nf_available()
        self.log.info(f"NextflowExecutor: Using Nextflow version: {self.nf_version}")

    def execute_workflow(self, nf_script_path, workspace_path, job_dir):
        nf_command = self.build_nf_command(nf_script_path, workspace_path)

        try:
            self._start_nf_process(nf_command, job_dir)
        except Exception as error:
            self.log.exception(f"start_nf_workflow: \n{error}")
            raise error

    def is_nf_available(self):
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
        except Exception:
            self.log.exception("error in is_nextflow_available. \
                Nextflow installation not found!")
            return None

        nf_version = self.parse_nf_version(ver_process.stdout)

        return nf_version

    @staticmethod
    def parse_nf_version(version_string):
        regex_pattern = r"nextflow version\s*([\d.]+)"
        nf_version = regex_search(regex_pattern, version_string).group(1)

        if nf_version:
            return nf_version

        return None

    @staticmethod
    def build_nf_command(nf_script_path, workspace_path):
        nf_command = "nextflow -bg"
        nf_command += f" run {nf_script_path}"
        nf_command += f" --workspace {workspace_path}/"
        nf_command += f" --mets {workspace_path}/mets.xml"
        nf_command += " -with-report"

        return nf_command

    def _start_nf_process(self, nf_command, job_dir):
        # Must be refined
        nf_out = f'{job_dir}/nextflow_out.txt'
        nf_err = f'{job_dir}/nextflow_err.txt'

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
            self.log.exception(f"Nextflow process failed to start: {error}")

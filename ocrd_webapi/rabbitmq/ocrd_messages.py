# Check here for more details: Message structure #139

class OcrdRequestMessage:
    def __init__(
            self,
            processor_name,
            job_id,
            workspace,
            input_file_grp,
            output_file_grp,
            page_id,
            should_overwrite,
            processor_parameters,
            level_of_log,
            profiling_path,
            result_queue_name
    ):
        # "ocrd-.*"
        self.processor_name = processor_name
        # uuid
        self.job_id = job_id
        # uuid or absolute path
        self.workspace = workspace
        # "OCR-D-.*"
        self.input_file_grp = input_file_grp
        # "OCR-D-.*"
        self.output_file_grp = output_file_grp
        # e.g., "PHYS_0005..PHYS_0010" will process only pages between 5-10
        self.page_id = page_id
        # Should overwrite mets file if files exist
        self.overwrite = should_overwrite
        # Dictionary with parameter keys and values
        self.processor_parameters = processor_parameters
        # e.g., "INFO"
        self.log_level = level_of_log,
        # e.g., "./logs/resource-usage.txt"
        self.save_profiling_to = profiling_path
        # e.g., "ocrd-cis-ocropy-binarize-result"
        self.result_queue = result_queue_name


class OcrdResponseMessage:
    def __init__(self, job_id, status, path_to_mets):
        self.job_id = job_id
        self.status = status
        self.workspace = path_to_mets

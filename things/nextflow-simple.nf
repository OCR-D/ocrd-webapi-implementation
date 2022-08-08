// enables a syntax extension that allows definition of module libraries
nextflow.enable.dsl = 2


// pipeline parameters
params.venv = "\$HOME/venv37-ocrd/bin/activate"
params.workspace = "$projectDir/ocrd-workspace/"
params.mets = "$projectDir/ocrd-workspace/mets.xml"

process ocrd_dummy {
	maxForks 1

	input:
		path mets_file
		val input_dir
		val output_dir

	output:
		val output_dir

	script:
	"""
	source "${params.venv}"
	ocrd-dummy -I ${input_dir} -O ${output_dir}
	deactivate
	"""
}

workflow {
	main:
		ocrd_dummy(params.mets, "OCR-D-IMG", "OCR-D-DUMMY")
}

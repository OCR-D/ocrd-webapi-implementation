nextflow.enable.dsl = 2

params.workspace_path = "$projectDir/ocrd-workspace/"
params.mets_path = "$projectDir/ocrd-workspace/mets.xml"
params.input_group = "OCR-D-IMG"
params.docker_pwd = "/ocrd-workspace"
params.docker_volume = "$params.workspace_path:$params.docker_pwd"
params.docker_models_dir = "/usr/local/share/ocrd-resources"
params.models_path = "\$HOME/ocrd_models"
params.docker_models = "$params.models_path:$params.docker_models_dir"
params.docker_image = "ocrd/all:maximum"
params.docker_command = "docker run --rm -u \$(id -u) -v $params.docker_volume -v $params.docker_models -w $params.docker_pwd -- $params.docker_image"

process ocrd_cis_ocropy_binarize_0 {
  maxForks 1

  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    path mets_file

  script:
    """
    ${params.docker_command} ocrd-cis-ocropy-binarize -I ${input_dir} -O ${output_dir}
    """
}

process ocrd_anybaseocr_crop_1 {
  maxForks 1

  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    path mets_file

  script:
    """
    ${params.docker_command} ocrd-anybaseocr-crop -I ${input_dir} -O ${output_dir}
    """
}

process ocrd_skimage_binarize_2 {
  maxForks 1

  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    path mets_file

  script:
    """
    ${params.docker_command} ocrd-skimage-binarize -I ${input_dir} -O ${output_dir} -P method li
    """
}

process ocrd_skimage_denoise_3 {
  maxForks 1

  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    path mets_file

  script:
    """
    ${params.docker_command} ocrd-skimage-denoise -I ${input_dir} -O ${output_dir} -P level-of-operation page
    """
}

process ocrd_tesserocr_deskew_4 {
  maxForks 1

  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    path mets_file

  script:
    """
    ${params.docker_command} ocrd-tesserocr-deskew -I ${input_dir} -O ${output_dir} -P operation_level page
    """
}

process ocrd_cis_ocropy_segment_5 {
  maxForks 1

  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    path mets_file

  script:
    """
    ${params.docker_command} ocrd-cis-ocropy-segment -I ${input_dir} -O ${output_dir} -P level-of-operation page
    """
}

process ocrd_cis_ocropy_dewarp_6 {
  maxForks 1

  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    path mets_file

  script:
    """
    ${params.docker_command} ocrd-cis-ocropy-dewarp -I ${input_dir} -O ${output_dir}
    """
}

process ocrd_calamari_recognize_7 {
  maxForks 1

  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    path mets_file

  script:
    """
    ${params.docker_command} ocrd-calamari-recognize -I ${input_dir} -O ${output_dir} -P checkpoint_dir qurator-gt4histocr-1.0
    """
}

workflow {
  main:
    ocrd_cis_ocropy_binarize_0(params.mets_path, params.input_group, "OCR-D-BIN")
    ocrd_anybaseocr_crop_1(ocrd_cis_ocropy_binarize_0.out, "OCR-D-BIN", "OCR-D-CROP")
    ocrd_skimage_binarize_2(ocrd_anybaseocr_crop_1.out, "OCR-D-CROP", "OCR-D-BIN2")
    ocrd_skimage_denoise_3(ocrd_skimage_binarize_2.out, "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
    ocrd_tesserocr_deskew_4(ocrd_skimage_denoise_3.out, "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
    ocrd_cis_ocropy_segment_5(ocrd_tesserocr_deskew_4.out, "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
    ocrd_cis_ocropy_dewarp_6(ocrd_cis_ocropy_segment_5.out, "OCR-D-SEG", "OCR-D-SEG-LINE-RESEG-DEWARP")
    ocrd_calamari_recognize_7(ocrd_cis_ocropy_dewarp_6.out, "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
}


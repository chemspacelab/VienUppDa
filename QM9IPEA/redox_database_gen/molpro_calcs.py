import os

from .utils import default_if_key_absent, insert_kwargs, num_omp_procs, timechecked_Popen


class TemplateCalculator:
    def __init__(self, template_file, exec_command="molpro"):
        template_input = open(template_file, "r")
        self.template_lines = template_input.read()
        self.exec_command = exec_command
        template_input.close()

    def make_calc(self, **kw_params):
        nMPI_procs = default_if_key_absent(kw_params, "NMPI_PROCS", num_omp_procs())
        nOMP_threads = default_if_key_absent(kw_params, "NOMP_THREADS", 1)
        input_file_string = insert_kwargs(self.template_lines, **kw_params)
        input_file_name = kw_params["CALC_NAME"] + ".inp"
        if os.path.isfile(input_file_name):  # the calculation has already been done
            return None
        else:
            input_file = open(input_file_name, "w")
            input_file.write(input_file_string)
            input_file.close()
            return timechecked_Popen(
                [
                    self.exec_command,
                    "-n",
                    str(nMPI_procs),
                    "-t",
                    str(nOMP_threads),
                    "-W",
                    kw_params["FULL_WORKDIR"],
                    "-d",
                    kw_params["SCRATCH_DIR"],
                    "-I",
                    kw_params["FULL_WORKDIR"],
                    input_file_name,
                ],
                script_name="molpro_" + kw_params["CALC_NAME"] + ".sh",
                time_log_output=kw_params["CALC_NAME"] + ".timestamps",
                dependencies=default_if_key_absent(kw_params, "DEPENDS", []),
            )

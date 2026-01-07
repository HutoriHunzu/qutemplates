# from qm import generate_qua_script, Program
#
#
# def generate_debug_script(program: Program,
#                            config: dict):
#
#     debug_script = generate_qua_script(program, config)
#     debug_script_as_str = debug_script.partition('\n\n\n')[0]
#     debug_script_as_dict_formatted = dict(enumerate(debug_script_as_str.replace('"', "'").split('\n')))
#
#     return debug_script, debug_script_as_dict_formatted


def debug_script_to_dict(debug_script: str) -> dict:
    debug_script_as_str = debug_script.partition('\n\n\n')[0]
    return dict(enumerate(debug_script_as_str.replace('"', "'").split('\n')))

import re


def work_folder_to_name(input_string: str) -> str:
    last_space_index = input_string.rfind(" ")
    return input_string[:last_space_index]


def work_folder_to_id(input_string: str) -> str:
    last_space_index = input_string.rfind(" ")
    return input_string[last_space_index + 1 :]


def sanitize_path(input_string: str) -> str:
    return re.sub(r'[\\/:"*?<>|]', "", input_string)

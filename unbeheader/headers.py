import os
from re import Pattern

from . import SUPPORTED_FILES
from .config import get_config
from .util import cformat


def update_header(file_path: str, year: int, ci: bool = False) -> bool:
    """Update the header of a file."""
    config = get_config(file_path, year)
    ext = file_path.rsplit('.', 1)[-1]
    if ext not in SUPPORTED_FILES or not os.path.isfile(file_path):
        return False
    if os.path.basename(file_path)[0] == '.':
        return False
    return _do_update_header(file_path, config, SUPPORTED_FILES[ext]['regex'], SUPPORTED_FILES[ext]['comments'], ci)


def _generate_header(data: dict) -> str:
    if 'start_year' not in data:
        data['start_year'] = data['end_year']
    if data['start_year'] == data['end_year']:
        data['dates'] = data['start_year']
    else:
        data['dates'] = '{} - {}'.format(data['start_year'], data['end_year'])
    comment = '\n'.join(line.rstrip() for line in data['header'].format(**data).strip().splitlines())
    return f'{comment}\n'


def _do_update_header(file_path: str, config: dict, regex: Pattern[str], comments: dict, ci: bool) -> bool:
    found = False
    with open(file_path) as file_read:
        content = orig_content = file_read.read()
        if not content.strip():
            return False
        shebang_line = None
        if content.startswith('#!/'):
            shebang_line, content = content.split('\n', 1)
        for match in regex.finditer(content):
            if config['substring'] in match.group():
                found = True
                match_end = content[match.end():].lstrip()
                match_end = f'\n{match_end}' if match_end else match_end
                if not content[:match.start()].strip() and not match_end.strip():
                    # file is otherwise empty, we do not want a header in there
                    content = ''
                else:
                    content = content[:match.start()] + _generate_header(comments | config) + match_end
        if shebang_line:
            content = shebang_line + '\n' + content
    if content != orig_content:
        msg = 'Incorrect header in {}' if ci else cformat('%{green!}Updating header of %{blue!}{}')
        print(msg.format(os.path.relpath(file_path)))
        if not ci:
            with open(file_path, 'w') as file_write:
                file_write.write(content)
        return True
    elif not found:
        msg = 'Missing header in {}' if ci else cformat('%{red!}Missing header%{reset} in %{blue!}{}')
        print(msg.format(os.path.relpath(file_path)))
        return True

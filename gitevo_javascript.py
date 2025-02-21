from gitevo import GitEvo, ParsedCommit

def as_str(text: bytes) -> str:
    return text.decode('utf-8')

evo = GitEvo(title='JavaScript', project_path='./projects_js', file_extension='.js', date_unit='year', since_year=2021)


@evo.metric('Analyzed JavaScript files', aggregate='sum')
def files(commit: ParsedCommit):
    return len(commit.parsed_files)


@evo.metric('Classes', aggregate='sum', categorical=True)
def data_structures(commit: ParsedCommit):
    return commit.node_types(['class_declaration'])


@evo.metric('Functions/methods', aggregate='sum', categorical=True)
def definitions(commit: ParsedCommit):
    method_nodes = ['function_declaration', 'method_definition', 'generator_function_declaration', 
                    'arrow_function', 'generator_function', 'function_expression']
    return commit.node_types(method_nodes)


@evo.metric('Variable declarations', aggregate='sum', categorical=True, version_chart='donut')
def for_while(commit: ParsedCommit):
    return commit.node_types(['const', 'let', 'var'])


@evo.metric('Conditional statements', aggregate='sum', categorical=True, version_chart='donut')
def for_while(commit: ParsedCommit):
    return commit.node_types(['if_statement', 'switch_statement'])


@evo.metric('Loops', aggregate='sum', categorical=True, version_chart='donut')
def for_while(commit: ParsedCommit):
    return commit.node_types(['for_statement', 'while_statement', 'for_in_statement', 'do_statement'])


@evo.metric('continue vs. break', aggregate='sum', categorical=True)
def data_structures(commit: ParsedCommit):
    return commit.node_types(['break_statement', 'continue_statement'])


@evo.metric('Exception statements', aggregate='sum', categorical=True)
def data_structures(commit: ParsedCommit):
    return commit.node_types(['try_statement', 'throw_statement'])


@evo.metric('Await expression', aggregate='sum', categorical=True)
def data_structures(commit: ParsedCommit):
    return commit.node_types(['await_expression'])


@evo.metric('Empty statement', aggregate='sum', categorical=True)
def data_structures(commit: ParsedCommit):
    return commit.node_types(['empty_statement'])


@evo.metric('Comments', aggregate='sum', categorical=True)
def data_structures(commit: ParsedCommit):
    return commit.node_types(['comment'])


evo.run()

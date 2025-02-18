from gitevo import GitEvo, ParsedCommit

evo = GitEvo(project_path='./projects_python', file_extension='.py', date_unit='year', since_year=2021)

@evo.metric('Analyzed files', aggregate='sum', file_extension='.js')
def files(commit: ParsedCommit):
    return len(commit.parsed_files)

@evo.metric('Most used data structures', aggregate='sum', categorical=True)
def data_structure(commit: ParsedCommit):
    return commit.node_types(['dictionary', 'list', 'set', 'tuple'])

@evo.metric('Most used comprehensions', aggregate='sum', categorical=True)
def comprehension(commit: ParsedCommit):
    return commit.node_types(['dictionary_comprehension', 'list_comprehension', 'set_comprehension'])

@evo.metric('Most used control flows', aggregate='sum', categorical=True)
def control_flow(commit: ParsedCommit):
    return commit.node_types(['for_statement', 'while_statement', 'if_statement', 'try_statement', 'match_statement', 'with_statement'])

@evo.metric('for vs. while', aggregate='sum', categorical=True)
def for_while(commit: ParsedCommit):
    return commit.node_types(['for_statement', 'while_statement'])

@evo.metric('continue vs. break', aggregate='sum', categorical=True)
def continue_break(commit: ParsedCommit):
    return commit.node_types(['break_statement', 'continue_statement'])

@evo.metric('integer vs. float', aggregate='sum', categorical=True)
def int_float(commit: ParsedCommit):
    return commit.node_types(['integer', 'float'])

@evo.metric('Function LOC (median)', aggregate='median')
def functions(commit: ParsedCommit):
    return commit.loc('function_definition', 'median')

@evo.metric('return vs. yield', aggregate='sum', categorical=True)
def return_yield(commit: ParsedCommit):
    return commit.node_types(['return_statement', 'yield'])

@evo.metric('Exceptions', aggregate='sum', categorical=True)
def exceptions(commit: ParsedCommit):
    return commit.node_types(['try_statement', 'raise_statement'])

@evo.metric('Most used import types', categorical=True)
def imports(commit: ParsedCommit):
    return commit.node_types(['import_statement', 'import_from_statement', 'future_import_statement'])

@evo.metric('Typed and default parameters', aggregate='sum', categorical=True)
def parameter_type(commit: ParsedCommit):
    return commit.node_types(['default_parameter', 'typed_parameter', 'typed_default_parameter'])

@evo.metric('Parameter dictionary vs. list splat pattern', aggregate='sum', categorical=True)
def parameter_splat_pattern(commit: ParsedCommit):
    return commit.node_types(['dictionary_splat_pattern', 'list_splat_pattern'])

@evo.metric('Decorated definitions', aggregate='sum')
def asserts(commit: ParsedCommit):
    return commit.count_nodes(['decorated_definition'])

@evo.metric('assert', aggregate='sum')
def asserts(commit: ParsedCommit):
    return commit.count_nodes(['assert_statement'])

@evo.metric('lambda', aggregate='sum')
def lambdas(commit: ParsedCommit):
    return commit.count_nodes(['lambda'])

@evo.metric('await', aggregate='sum')
def awaits(commit: ParsedCommit):
    return commit.count_nodes(['await'])

@evo.metric('pass', aggregate='sum')
def passes(commit: ParsedCommit):
    return commit.count_nodes(['pass_statement'])

evo.run()

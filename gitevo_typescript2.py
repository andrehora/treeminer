from gitevo import GitEvo, ParsedCommit

def as_str(text: bytes) -> str:
    return text.decode('utf-8')

evo = GitEvo(title='TypeScript', html_filename='index_ts.html', 
             project_path='./projects_typescript', file_extension='.ts',
             date_unit='year', since_year=2020)


@evo.metric('Analyzed TypeScript files', aggregate='sum')
def files(commit: ParsedCommit):
    return len(commit.parsed_files)

@evo.metric('LOC', aggregate='sum')
def files(commit: ParsedCommit):
    return commit.loc



@evo.metric('let', aggregate='median', group='let vs. var')
def variable_declarations(commit: ParsedCommit):
    return commit.count_nodes(['let']) / (commit.loc / 1000)

@evo.metric('var', aggregate='median', group='let vs. var')
def variable_declarations(commit: ParsedCommit):
    return commit.count_nodes(['var']) / (commit.loc / 1000)



@evo.metric('function declaration', aggregate='median', group='functions')
def definitions(commit: ParsedCommit):
    return commit.count_nodes(['function_declaration']) / (commit.loc / 1000)

@evo.metric('function expression', aggregate='median', group='functions')
def definitions(commit: ParsedCommit):
    return commit.count_nodes(['function_expression']) / (commit.loc / 1000)

@evo.metric('arrow function', aggregate='median', group='functions')
def definitions(commit: ParsedCommit):
    return commit.count_nodes(['arrow_function']) / (commit.loc / 1000)



@evo.metric('if', aggregate='median', group='conditionals')
def conditionals(commit: ParsedCommit):
    return commit.count_nodes(['if_statement']) / (commit.loc / 1000)

@evo.metric('switch', aggregate='median', group='conditionals')
def conditionals(commit: ParsedCommit):
    return commit.count_nodes(['switch_statement']) / (commit.loc / 1000)

@evo.metric('ternary', aggregate='median', group='conditionals')
def conditionals(commit: ParsedCommit):
    return commit.count_nodes(['ternary_expression']) / (commit.loc / 1000)



@evo.metric('for', aggregate='median', group='loops')
def for_while(commit: ParsedCommit):
    return commit.count_nodes(['for_statement']) / (commit.loc / 1000)

@evo.metric('while', aggregate='median', group='loops')
def for_while(commit: ParsedCommit):
    return commit.count_nodes(['while_statement']) / (commit.loc / 1000)

@evo.metric('for in', aggregate='median', group='loops')
def for_while(commit: ParsedCommit):
    return commit.count_nodes(['for_in_statement']) / (commit.loc / 1000)

@evo.metric('do while', aggregate='median', group='loops')
def for_while(commit: ParsedCommit):
    return commit.count_nodes(['do_statement']) / (commit.loc / 1000)



@evo.metric('continue', aggregate='median', group='continue vs. break')
def continue_break(commit: ParsedCommit):
    return commit.count_nodes(['continue_statement']) / (commit.loc / 1000)

@evo.metric('break', aggregate='median', group='continue vs. break')
def continue_break(commit: ParsedCommit):
    return commit.count_nodes(['break_statement']) / (commit.loc / 1000)



@evo.metric('try', aggregate='median', group='try vs. throw')
def exceptions(commit: ParsedCommit):
    return commit.count_nodes(['try_statement']) / (commit.loc / 1000)

@evo.metric('throw', aggregate='median', group='try vs. throw')
def exceptions(commit: ParsedCommit):
    return commit.count_nodes(['throw_statement']) / (commit.loc / 1000)



@evo.metric('interface', aggregate='median', group='interface vs. type')
def type_definitions(commit: ParsedCommit):
    return commit.count_nodes(['interface_declaration']) / (commit.loc / 1000)

@evo.metric('type', aggregate='median', group='interface vs. type')
def type_definitions(commit: ParsedCommit):
    return commit.count_nodes(['type_alias_declaration']) / (commit.loc / 1000)



@evo.metric('any', aggregate='median', group='any vs. unknown')
def type_definitions(commit: ParsedCommit):
    return commit.count_nodes(['any']) / (commit.loc / 1000)

@evo.metric('unknown', aggregate='median', group='any vs. unknown')
def type_definitions(commit: ParsedCommit):
    return commit.count_nodes(['unknown']) / (commit.loc / 1000)



@evo.metric('required', aggregate='median', group='required vs. optional parameter')
def req_opt_parameters(commit: ParsedCommit):
    return commit.count_nodes(['required_parameter']) / (commit.loc / 1000)

@evo.metric('optional', aggregate='median', group='required vs. optional parameter')
def req_opt_parameters(commit: ParsedCommit):
    return commit.count_nodes(['optional_parameter']) / (commit.loc / 1000)

evo.run()
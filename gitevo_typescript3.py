from gitevo import GitEvo, ParsedCommit

def as_str(text: bytes) -> str:
    return text.decode('utf-8')

def ratio(a: int, b: int) -> int:
    if b == 0:
        return 0
    return round(a/b*100, 0)

evo = GitEvo(title='TypeScript', html_filename='index_ts.html', 
             project_path='./projects_typescript', file_extension='.ts',
             date_unit='year', since_year=2015)


@evo.metric('TypeScript files', aggregate='sum')
def files(commit: ParsedCommit):
    return len(commit.parsed_files)

@evo.metric('LOC', aggregate='sum')
def files(commit: ParsedCommit):
    return commit.loc


@evo.metric('var', aggregate='median', group='let vs. var')
def variable_declarations(commit: ParsedCommit):
    var_count = commit.count_nodes(['var'])
    total = commit.count_nodes(['var', 'let'])
    return ratio(var_count, total)

@evo.metric('let', aggregate='median', group='let vs. var')
def variable_declarations(commit: ParsedCommit):
    let_count = commit.count_nodes(['let'])
    total = commit.count_nodes(['var', 'let'])
    return ratio(let_count, total)


@evo.metric('arrow function', aggregate='median', group='functions')
def definitions(commit: ParsedCommit):
    arrow_function_count = commit.count_nodes(['arrow_function'])
    total = commit.count_nodes(['arrow_function', 'function_declaration', 'function_expression'])
    return ratio(arrow_function_count, total)

@evo.metric('function declaration', aggregate='median', group='functions')
def definitions(commit: ParsedCommit):
    function_declaration_count = commit.count_nodes(['function_declaration'])
    total = commit.count_nodes(['arrow_function', 'function_declaration', 'function_expression'])
    return ratio(function_declaration_count, total)

@evo.metric('function expression', aggregate='median', group='functions')
def definitions(commit: ParsedCommit):
    function_expression_count = commit.count_nodes(['function_expression'])
    total = commit.count_nodes(['arrow_function', 'function_declaration', 'function_expression'])
    return ratio(function_expression_count, total)


@evo.metric('interface', aggregate='median', group='interface vs. type')
def type_definitions(commit: ParsedCommit):
    interface_count = commit.count_nodes(['interface_declaration'])
    total = commit.count_nodes(['interface_declaration', 'type_alias_declaration'])
    return ratio(interface_count, total)

@evo.metric('type', aggregate='median', group='interface vs. type')
def type_definitions(commit: ParsedCommit):
    type_count = commit.count_nodes(['type_alias_declaration'])
    total = commit.count_nodes(['interface_declaration', 'type_alias_declaration'])
    return ratio(type_count, total)


@evo.metric('any', aggregate='median', group='any vs. unknown')
def type_definitions(commit: ParsedCommit):
    any_count = commit.count_nodes(['any'])
    total = commit.count_nodes(['any', 'unknown'])
    return ratio(any_count, total)

@evo.metric('unknown', aggregate='median', group='any vs. unknown')
def type_definitions(commit: ParsedCommit):
    unknown_count = commit.count_nodes(['unknown'])
    total = commit.count_nodes(['any', 'unknown'])
    return ratio(unknown_count, total)


evo.run()
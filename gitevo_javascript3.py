from gitevo import GitEvo, ParsedCommit

def as_str(text: bytes) -> str:
    return text.decode('utf-8')

def ratio(a: int, b: int) -> int:
    if b == 0:
        return 0
    return round(a/b*100, 0)

evo = GitEvo(title='JavaScript', html_filename='index_js.html', 
             project_path='./projects_javascript', file_extension='.js', 
             date_unit='year', since_year=2020)


@evo.metric('JavaScript files', aggregate='sum')
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

evo.run()

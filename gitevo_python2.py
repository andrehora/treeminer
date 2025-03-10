from gitevo import GitEvo, ParsedCommit
import tree_sitter_python


def as_str(text: bytes) -> str:
    return text.decode('utf-8')

evo = GitEvo(title='Python', html_filename='index_python.html', 
             repo='./projects_python', extension='.py', 
             date_unit='year', since_year=2020)
# evo.add_language('.py', tree_sitter_python.language())


@evo.metric('Analyzed Python files', aggregate='sum')
def files(commit: ParsedCommit):
    return len(commit.parsed_files)

@evo.metric('LOC', aggregate='sum')
def files(commit: ParsedCommit):
    return commit.loc



@evo.metric('@classmethod', aggregate='median', group='@classmethod vs. @staticmethod')
def definitions(commit: ParsedCommit):
    decorated_definitions = commit.find_nodes_by_type(['decorated_definition'])
    decorated_functions = [decorated_definition for decorated_definition in decorated_definitions if decorated_definition.child_by_field_name('definition').type == 'function_definition']
    classmethods = [decorated_function for decorated_function in decorated_functions if as_str(decorated_function.child(0).text).startswith('@classmethod')]
    return len(classmethods) / (commit.loc / 1000)

@evo.metric('@staticmethod', aggregate='median', group='@classmethod vs. @staticmethod')
def definitions(commit: ParsedCommit):
    decorated_definitions = commit.find_nodes_by_type(['decorated_definition'])
    decorated_functions = [decorated_definition for decorated_definition in decorated_definitions if decorated_definition.child_by_field_name('definition').type == 'function_definition']
    staticmethods = [decorated_function for decorated_function in decorated_functions if as_str(decorated_function.child(0).text).startswith('@staticmethod')]
    return len(staticmethods) / (commit.loc / 1000)



@evo.metric('import', aggregate='median', group='import vs. import from')
def imports(commit: ParsedCommit):
    return commit.count_nodes(['import_statement']) / (commit.loc / 1000)

@evo.metric('import from', aggregate='median', group='import vs. import from')
def imports(commit: ParsedCommit):
    return commit.count_nodes(['import_from_statement']) / (commit.loc / 1000)



@evo.metric('try', aggregate='median', group='try vs. raise')
def exceptions(commit: ParsedCommit):
    return commit.count_nodes(['try_statement']) / (commit.loc / 1000)

@evo.metric('raise', aggregate='median', group='try vs. raise')
def exceptions(commit: ParsedCommit):
    return commit.count_nodes(['raise_statement']) / (commit.loc / 1000)



@evo.metric('for', aggregate='median', group='loops')
def for_while(commit: ParsedCommit):
    return commit.count_nodes(['for_statement']) / (commit.loc / 1000)

@evo.metric('while', aggregate='median', group='loops')
def for_while(commit: ParsedCommit):
    return commit.count_nodes(['while_statement']) / (commit.loc / 1000)

@evo.metric('for in', aggregate='median', group='loops')
def for_while(commit: ParsedCommit):
    return commit.count_nodes(['for_in_clause']) / (commit.loc / 1000)



@evo.metric('continue', aggregate='median', group='continue vs. break')
def continue_break(commit: ParsedCommit):
    return commit.count_nodes(['continue_statement']) / (commit.loc / 1000)

@evo.metric('break', aggregate='median', group='continue vs. break')
def continue_break(commit: ParsedCommit):
    return commit.count_nodes(['break_statement']) / (commit.loc / 1000)



@evo.metric('assert', aggregate='median')
def asserts(commit: ParsedCommit):
    return commit.count_nodes(['assert_statement']) / (commit.loc / 1000)


evo.run()

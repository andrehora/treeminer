from gitevo import GitEvo, ParsedCommit

def as_str(text: bytes) -> str:
    return text.decode('utf-8')

evo = GitEvo(title='Java', html_filename='index_java.html', 
             repo='./projects_java', extension='.java',
             date_unit='year', since_year=2020)


@evo.metric('Analyzed Java files', aggregate='sum')
def files(commit: ParsedCommit):
    return len(commit.parsed_files)

@evo.metric('LOC', aggregate='sum')
def files(commit: ParsedCommit):
    return commit.loc



@evo.metric('if', aggregate='median', group='conditionals')
def conditionals(commit: ParsedCommit):
    return commit.count_nodes(['if_statement']) / (commit.loc / 1000)

@evo.metric('switch', aggregate='median', group='conditionals')
def conditionals(commit: ParsedCommit):
    return commit.count_nodes(['switch_expression']) / (commit.loc / 1000)

@evo.metric('ternary', aggregate='median', group='conditionals')
def conditionals(commit: ParsedCommit):
    return commit.count_nodes(['ternary_expression']) / (commit.loc / 1000)



@evo.metric('switch_block_statement_group', aggregate='median', group='switches')
def conditionals(commit: ParsedCommit):
    return commit.count_nodes(['switch_block_statement_group']) / (commit.loc / 1000)

@evo.metric('switch_rule', aggregate='median', group='switches')
def conditionals(commit: ParsedCommit):
    return commit.count_nodes(['switch_rule']) / (commit.loc / 1000)



@evo.metric('for', aggregate='median', group='loops')
def for_while(commit: ParsedCommit):
    return commit.count_nodes(['for_statement']) / (commit.loc / 1000)

@evo.metric('while', aggregate='median', group='loops')
def for_while(commit: ParsedCommit):
    return commit.count_nodes(['while_statement']) / (commit.loc / 1000)

@evo.metric('for in', aggregate='median', group='loops')
def for_while(commit: ParsedCommit):
    return commit.count_nodes(['enhanced_for_statement']) / (commit.loc / 1000)

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



@evo.metric('assert', aggregate='median')
def asserts(commit: ParsedCommit):
    return commit.count_nodes(['assert_statement']) / (commit.loc / 1000)

evo.run()
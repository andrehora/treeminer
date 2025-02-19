from gitevo import GitEvo, ParsedCommit

evo = GitEvo(title='Python', project_path='./projects_python/rich', file_extension='.py', date_unit='year', since_year=2021)


@evo.metric('Analyzed Python files', project_aggregate='sum')
def files(commit: ParsedCommit):
    return len(commit.parsed_files)


@evo.metric('Most used data structures', project_aggregate='sum', categorical=True)
def data_structure(commit: ParsedCommit):
    return commit.node_types(['dictionary', 'list', 'set', 'tuple'])


@evo.metric('Most used comprehensions', project_aggregate='sum', categorical=True)
def comprehension(commit: ParsedCommit):
    return commit.node_types(['dictionary_comprehension', 'list_comprehension', 'set_comprehension'])


@evo.metric('Definitions', project_aggregate='sum', categorical=True)
def asserts(commit: ParsedCommit):
    return commit.node_types(['class_definition', 'function_definition', 'decorated_definition'])


@evo.metric('class_definition_loc', project_aggregate='median', group='Median definition LOC')
def functions(commit: ParsedCommit):
    return commit.loc('class_definition', 'median')


@evo.metric('function_definition_loc', project_aggregate='median', group='Median definition LOC')
def functions(commit: ParsedCommit):
    return commit.loc('function_definition', 'median')


@evo.metric('decorated_definition_loc', project_aggregate='median', group='Median definition LOC')
def functions(commit: ParsedCommit):
    return commit.loc('decorated_definition', 'median')


@evo.metric('Import statements', categorical=True, version_chart='donut')
def imports(commit: ParsedCommit):
    return commit.node_types(['import_statement', 'import_from_statement', 'future_import_statement'])


@evo.metric('Exception statements', project_aggregate='sum', categorical=True)
def exceptions(commit: ParsedCommit):
    return commit.node_types(['try_statement', 'raise_statement'])


@evo.metric('Control flow statements', project_aggregate='sum', categorical=True)
def control_flow(commit: ParsedCommit):
    return commit.node_types(['for_statement', 'while_statement', 'if_statement', 'try_statement', 'match_statement', 'with_statement'])


@evo.metric('for vs. while', project_aggregate='sum', categorical=True, version_chart='donut')
def for_while(commit: ParsedCommit):
    return commit.node_types(['for_statement', 'while_statement'])


@evo.metric('continue vs. break', project_aggregate='sum', categorical=True, version_chart='donut')
def continue_break(commit: ParsedCommit):
    return commit.node_types(['break_statement', 'continue_statement'])


@evo.metric('integer vs. float', project_aggregate='sum', categorical=True, version_chart='donut')
def int_float(commit: ParsedCommit):
    return commit.node_types(['integer', 'float'])


@evo.metric('return vs. yield', project_aggregate='sum', categorical=True, version_chart='donut')
def return_yield(commit: ParsedCommit):
    return commit.node_types(['return_statement', 'yield'])


@evo.metric('Typed/default parameters', project_aggregate='sum', categorical=True)
def parameter_type(commit: ParsedCommit):
    return commit.node_types(['default_parameter', 'typed_parameter', 'typed_default_parameter'])


@evo.metric('Dictionary/list splat patterns in parameters', project_aggregate='sum', categorical=True)
def parameter_splat_pattern(commit: ParsedCommit):
    return commit.node_types(['dictionary_splat_pattern', 'list_splat_pattern'])


@evo.metric('Keyword: assert', project_aggregate='sum')
def asserts(commit: ParsedCommit):
    return commit.count_nodes(['assert_statement'])


@evo.metric('Keyword: lambda', project_aggregate='sum')
def lambdas(commit: ParsedCommit):
    return commit.count_nodes(['lambda'])


@evo.metric('Keyword: await', project_aggregate='sum')
def awaits(commit: ParsedCommit):
    return commit.count_nodes(['await'])


@evo.metric('Keyword: pass', project_aggregate='sum')
def passes(commit: ParsedCommit):
    return commit.count_nodes(['pass_statement'])


@evo.metric('ellipsis', project_aggregate='sum')
def passes(commit: ParsedCommit):
    return commit.count_nodes(['ellipsis'])


@evo.metric('Aliased imports', project_aggregate='sum')
def imports(commit: ParsedCommit):
    return commit.count_nodes(['aliased_import'])

evo.run()

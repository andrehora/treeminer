from gitevo import GitEvo, ParsedCommit

def as_str(text: bytes) -> str:
    return text.decode('utf-8')

evo = GitEvo(title='Java', project_path='./projects_java', file_extension='.java', date_unit='year', since_year=2021)


@evo.metric('Analyzed Java files', aggregate='sum')
def files(commit: ParsedCommit):
    return len(commit.parsed_files)


@evo.metric('Classes, interfaces, and records', aggregate='sum', categorical=True)
def type_definitions(commit: ParsedCommit):
    return commit.node_types(['class_declaration', 'interface_declaration', 'record_declaration'])


@evo.metric('Methods', aggregate='sum')
def type_definitions(commit: ParsedCommit):
    return commit.count_nodes(['method_declaration', 'constructor_declaration'])


# @evo.metric('Variable declarations: const, let, and var', aggregate='sum', categorical=True, version_chart='donut')
# def variable_declarations(commit: ParsedCommit):
#     return commit.node_types(['const', 'let', 'var'])


# @evo.metric('Variables: typed vs. untyped', aggregate='sum', categorical=True, version_chart='donut')
# def variables(commit: ParsedCommit):
#     return ['typed_var' if var.child_by_field_name('type') else 'untyped_var' for var in commit.find_nodes_by_type(['variable_declarator'])]


# @evo.metric('Function/method declarations', aggregate='sum', categorical=True)
# def function_definitions(commit: ParsedCommit):
#     nodes = ['function_declaration', 'method_definition', 'generator_function_declaration', 'arrow_function', 'generator_function', 'function_expression']
#     return commit.node_types(nodes)


# @evo.metric('Function/method signatures', aggregate='sum', categorical=True)
# def signatures(commit: ParsedCommit):
#     return commit.node_types(['function_signature', 'method_signature', 'abstract_method_signature'])


# @evo.metric('Function/method return types', aggregate='sum', categorical=True, version_chart='donut')
# def return_type(commit: ParsedCommit):
#     ts_nodes = ['abstract_method_signature', 'function_signature', 'method_signature', 'call_signature', 'function_type']
#     js_nodes = ['function_declaration', 'method_definition', 'generator_function_declaration', 'arrow_function', 'generator_function', 'function_expression']
#     nodes = ts_nodes+js_nodes
#     return ['return_type' if var.child_by_field_name('return_type') else 'no return_type' for var in commit.find_nodes_by_type(nodes)]


# @evo.metric('Parameters: typed vs. untyped', aggregate='sum', categorical=True, version_chart='donut')
# def parameters(commit: ParsedCommit):
#     return ['typed_param' if var.child_by_field_name('type') else 'untyped_param' for var in commit.find_nodes_by_type(['required_parameter', 'optional_parameter'])]


# @evo.metric('Parameters: required vs. optional', aggregate='sum', categorical=True, version_chart='donut')
# def req_opt_parameters(commit: ParsedCommit):
#     return commit.node_types(['required_parameter', 'optional_parameter'])


@evo.metric('Conditional statements', aggregate='sum', categorical=True)
def conditionals(commit: ParsedCommit):
    return commit.node_types(['if_statement', 'switch_expression', 'ternary_expression'])


@evo.metric('Switches', aggregate='sum', categorical=True)
def conditionals(commit: ParsedCommit):
    return commit.node_types(['switch_block_statement_group', 'switch_rule'])


@evo.metric('Loops', aggregate='sum', categorical=True, version_chart='donut')
def loops(commit: ParsedCommit):
    return commit.node_types(['for_statement', 'while_statement', 'enhanced_for_statement', 'do_statement'])


@evo.metric('continue vs. break', aggregate='sum', categorical=True)
def continue_break(commit: ParsedCommit):
    return commit.node_types(['break_statement', 'continue_statement'])


@evo.metric('Exception statements', aggregate='sum', categorical=True)
def expections(commit: ParsedCommit):
    return commit.node_types(['try_statement', 'throw_statement'])


@evo.metric('int vs. float', aggregate='sum', categorical=True, version_chart='donut')
def int_float(commit: ParsedCommit):
    return commit.node_types(['integral_type', 'floating_point_type'])


@evo.metric('Asserts', aggregate='sum')
def comments(commit: ParsedCommit):
    return commit.count_nodes(['assert_statement'])


@evo.metric('Comments', aggregate='sum', categorical=True)
def comments(commit: ParsedCommit):
    return commit.node_types(['block_comment', 'line_comment'])

evo.run()
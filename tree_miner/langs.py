import tree_sitter_python, tree_sitter_java, tree_sitter_javascript


# https://github.com/tree-sitter/tree-sitter-python/blob/master/src/node-types.json


# https://github.com/tree-sitter/tree-sitter-java/blob/master/src/node-types.json
class Java:
    name = 'java'
    extension = '.java'
    tree_sitter_grammar = tree_sitter_java

    import_nodes = ['import_declaration']
    class_nodes = ['class_declaration']
    method_nodes = ['method_declaration', 'constructor_declaration', 'compact_constructor_declaration']
    call_nodes = ['method_invocation', 'object_creation_expression']
    comment_nodes = ['line_comment', 'block_comment']

# https://github.com/tree-sitter/tree-sitter-javascript/blob/master/src/node-types.json
class JavaScript:
    name = 'javascript'
    extension = '.js'
    tree_sitter_grammar = tree_sitter_javascript

    import_nodes = ['import_statement']
    class_nodes = ['class_declaration', 'class']
    method_nodes = ['function_declaration', 'function', 'method_definition', 'generator_function_declaration', 
                    'arrow_function', 'generator_function', 'function_expression']
    call_nodes = ['call_expression']
    comment_nodes = ['comment']
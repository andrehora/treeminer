
# https://github.com/tree-sitter/tree-sitter-python/blob/master/src/node-types.json
python = {
    'imports': [],
    'comments': ['comment'],
    'classes': ['class_definition'],
    'methods': ['function_definition'],
    'attributes': [],
    'calls': ['call'],
    'decorators': '',

}

# https://github.com/tree-sitter/tree-sitter-java/blob/master/src/node-types.json
java = {
    'imports': [],
    'comments': ['line_comment', 
                 'block_comment'],
    'classes': ['class_declaration'],
    'methods': ['method_declaration', 
                'constructor_declaration', 
                'compact_constructor_declaration'],
    'calls': ['method_invocation',
              'object_creation_expression']
}

# https://github.com/tree-sitter/tree-sitter-javascript/blob/master/src/node-types.json
javascript = {
    'imports': [],
    'comments': ['comment'],
    'classes': ['class_declaration', 
                'class'],
    'methods': ['function_declaration', 
                'function', 
                'method_definition', 
                'generator_function_declaration', 
                'arrow_function', 
                'generator_function', 
                'function_expression'],
    'calls': ['call_expression']
}
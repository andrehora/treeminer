import tree_sitter_python, tree_sitter_java, tree_sitter_javascript
from tree_sitter import Node

class BaseMiner:

    import_nodes = []
    class_nodes = []
    method_nodes = []
    call_nodes = []
    comment_nodes = []
    
    def __init__(self, nodes: list[Node] | None = None):
        self.nodes = nodes
        if nodes is None:
            self.nodes = []

    @property
    def imports(self) -> list[Node]:
        return self.find_nodes_by_types(self.import_nodes)

    @property
    def classes(self) -> list[Node]:
        return self.find_nodes_by_types(self.class_nodes)

    @property
    def methods(self) -> list[Node]:
        return self.find_nodes_by_types(self.method_nodes)
    
    @property
    def calls(self) -> list[Node]:
        return self.find_nodes_by_types(self.call_nodes)
    
    @property
    def comments(self) -> list[Node]:
        return self.find_nodes_by_types(self.comment_nodes)
    
    def find_nodes_by_types(self, node_types: list[str]) -> list[Node]:
        nodes = []
        for node in self.nodes:
            if node.type in node_types:
                nodes.append(node)
        return nodes
    
# https://github.com/tree-sitter/tree-sitter-python/blob/master/src/node-types.json
class PythonMiner(BaseMiner):
    name = 'python'
    extension = 'py'
    tree_sitter_grammar = tree_sitter_python

    import_nodes = ['import_statement', 'import_from_statement', 'future_import_statement']
    class_nodes = ['class_definition']
    method_nodes = ['function_definition']
    call_nodes = ['call']
    comment_nodes = ['comment']

# https://github.com/tree-sitter/tree-sitter-javascript/blob/master/src/node-types.json
class JavaScriptMiner(BaseMiner):
    name = 'javascript'
    extension = 'js'
    tree_sitter_grammar = tree_sitter_javascript

    import_nodes = ['import_statement']
    class_nodes = ['class_declaration', 'class']
    method_nodes = ['function_declaration', 'function', 'method_definition', 'generator_function_declaration', 
                    'arrow_function', 'generator_function', 'function_expression']
    call_nodes = ['call_expression']
    comment_nodes = ['comment']

# https://github.com/tree-sitter/tree-sitter-java/blob/master/src/node-types.json
class JavaMiner(BaseMiner):
    name = 'java'
    extension = 'java'
    tree_sitter_grammar = tree_sitter_java

    import_nodes = ['import_declaration']
    class_nodes = ['class_declaration']
    method_nodes = ['method_declaration', 'constructor_declaration', 'compact_constructor_declaration']
    call_nodes = ['method_invocation', 'object_creation_expression']
    comment_nodes = ['line_comment', 'block_comment']

buildin_miners = [PythonMiner, JavaScriptMiner, JavaMiner]

import tree_sitter_python, tree_sitter_javascript, tree_sitter_java, tree_sitter_typescript
from tree_sitter import Node


class BaseMiner:

    import_nodes = []
    class_nodes = []
    method_nodes = []
    call_nodes = []
    comment_nodes = []
    
    def __init__(self, tree_nodes: list[Node] | None = None):
        self.tree_nodes = tree_nodes
        if tree_nodes is None:
            self.tree_nodes = []

    @property
    def errors(self) -> list[Node]:
        return [node for node in self.tree_nodes if node.is_error]

    @property
    def missings(self) -> list[Node]:
        return [node for node in self.tree_nodes if node.is_missing]
    
    @property
    def extras(self) -> list[Node]:
        return [node for node in self.tree_nodes if node.is_extra]
    
    @property
    def named(self) -> list[Node]:
        return [node for node in self.tree_nodes if node.is_named]

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
    
    def find_nodes_by_type(self, node_type: str) -> list[Node]:
        return self.find_nodes_by_types([node_type])
    
    def find_nodes_by_types(self, node_types: list[str]) -> list[Node]:
        nodes = []
        for node in self.tree_nodes:
            if node.type in node_types:
                nodes.append(node)
        return nodes
    
    def find_descendant_node_by_field_name(self, node: Node, name: str) -> Node | None:
        for desc_node in self.get_descendant_nodes(node):
            target_node = desc_node.child_by_field_name(name)
            if target_node is not None:
                return target_node
        return None
    
    def get_descendant_nodes(self, node: Node) -> list[Node]:
        descendants = []

        def traverse_node(current_node):
            descendants.append(current_node)
            for child in current_node.children:
                traverse_node(child)

        traverse_node(node)
        return descendants


# https://github.com/tree-sitter/tree-sitter-python/blob/master/src/node-types.json
class PythonMiner(BaseMiner):
    name = 'python'
    extension = 'py'
    tree_sitter_language = tree_sitter_python.language()

    import_nodes = ['import_statement', 'import_from_statement', 'future_import_statement']
    class_nodes = ['class_definition']
    method_nodes = ['function_definition']
    call_nodes = ['call']
    comment_nodes = ['comment']


# https://github.com/tree-sitter/tree-sitter-javascript/blob/master/src/node-types.json
class JavaScriptMiner(BaseMiner):
    name = 'javascript'
    extension = 'js'
    tree_sitter_language = tree_sitter_javascript.language()

    import_nodes = ['import_statement']
    class_nodes = ['class_declaration']
    method_nodes = ['function_declaration', 'method_definition', 'generator_function_declaration', 
                    'arrow_function', 'generator_function', 'function_expression']
    call_nodes = ['call_expression', 'new_expression']
    comment_nodes = ['comment']


# https://github.com/tree-sitter/tree-sitter-typescript/blob/master/typescript/src/node-types.json
class TypeScriptMiner(BaseMiner):
    name = 'typescript'
    extension = 'ts'
    tree_sitter_language = tree_sitter_typescript.language_typescript()

    # import_nodes = ['import_declaration']
    # class_nodes = ['class_declaration']
    # method_nodes = ['method_declaration', 'constructor_declaration', 'compact_constructor_declaration']
    # call_nodes = ['method_invocation', 'object_creation_expression']
    # comment_nodes = ['line_comment', 'block_comment']

# https://github.com/tree-sitter/tree-sitter-java/blob/master/src/node-types.json
class JavaMiner(BaseMiner):
    name = 'java'
    extension = 'java'
    tree_sitter_language = tree_sitter_java.language()

    import_nodes = ['import_declaration']
    class_nodes = ['class_declaration']
    method_nodes = ['method_declaration', 'constructor_declaration', 'compact_constructor_declaration']
    call_nodes = ['method_invocation', 'object_creation_expression']
    comment_nodes = ['line_comment', 'block_comment']

buildin_miners = [PythonMiner, JavaScriptMiner, TypeScriptMiner, JavaMiner]

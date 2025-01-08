from treeminer.repo import CodeParser
from treeminer.miners import PythonMiner, JavaScriptMiner, JavaMiner
from tests.extensions import FastAPIMiner


def read_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def python_miner(source_code):
    parser = CodeParser(source_code, PythonMiner.tree_sitter_grammar)
    return PythonMiner(list(parser.tree_nodes))

def fastapi_miner(source_code):
    parser = CodeParser(source_code, FastAPIMiner.tree_sitter_grammar)
    return FastAPIMiner(list(parser.tree_nodes))

def javascript_miner(source_code):
    parser = CodeParser(source_code, JavaScriptMiner.tree_sitter_grammar)
    return JavaScriptMiner(list(parser.tree_nodes))

def java_miner(source_code):
    parser = CodeParser(source_code, JavaMiner.tree_sitter_grammar)
    return JavaMiner(list(parser.tree_nodes))
import pytest
from treeminer.repo import CodeParser
from treeminer.miners import PythonMiner, JavaScriptMiner, JavaMiner


@pytest.fixture
def python_code():
    pass

@pytest.fixture
def javascript_code():
    pass

@pytest.fixture
def java_code():
    pass

@pytest.fixture
def python_miner(python_code):
    parser = CodeParser(python_code, PythonMiner.tree_sitter_grammar)
    return PythonMiner(parser.tree_nodes)

@pytest.fixture
def javascript_miner(javascript_code):
    parser = CodeParser(javascript_code, JavaScriptMiner.tree_sitter_grammar)
    return JavaScriptMiner(parser.tree_nodes)

@pytest.fixture
def java_miner(java_code):
    parser = CodeParser(java_code, JavaMiner.tree_sitter_grammar)
    return JavaMiner(parser.tree_nodes)
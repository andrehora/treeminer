import pytest
from treeminer.repo import CodeParser
from treeminer.miners import PythonMiner, JavaScriptMiner, JavaMiner


def read_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def python_miner(source_code):
    parser = CodeParser(source_code, PythonMiner.tree_sitter_grammar)
    return PythonMiner(parser.tree_nodes)


@pytest.fixture
def basic_python_code():
    return read_file('./tests/samples/basic_python.py')

@pytest.fixture
def basic_javascript_code():
    return read_file('./tests/samples/basic_javascript.js')

@pytest.fixture
def basic_java_code():
    return read_file('./tests/samples/basic_java.java')

# @pytest.fixture
# def python_ext():
#     return read_file('./tests/samples/extension_python_fastapi.py')

@pytest.fixture
def basic_python():
    return python_miner(read_file('./tests/samples/basic_python.py'))

@pytest.fixture
def basic_javascript(basic_javascript_code):
    parser = CodeParser(basic_javascript_code, JavaScriptMiner.tree_sitter_grammar)
    return JavaScriptMiner(parser.tree_nodes)

@pytest.fixture
def basic_java(basic_java_code):
    parser = CodeParser(basic_java_code, JavaMiner.tree_sitter_grammar)
    return JavaMiner(parser.tree_nodes)
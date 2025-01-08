def test_imports(basic_python):
    assert len(basic_python.imports) == 0

def test_classes(basic_python):
    assert len(basic_python.classes) == 1

def test_methods(basic_python):
    assert len(basic_python.methods) == 5

def test_calls(basic_python):
    assert len(basic_python.calls) == 6

def test_comments(basic_python):
    assert len(basic_python.comments) == 2

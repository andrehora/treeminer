def test_imports(basic_java):
    assert len(basic_java.imports) == 0

def test_classes(basic_java):
    assert len(basic_java.classes) == 1

def test_methods(basic_java):
    assert len(basic_java.methods) == 6

def test_calls(basic_java):
    assert len(basic_java.calls) == 6

def test_comments(basic_java):
    assert len(basic_java.comments) == 2
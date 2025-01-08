def test_imports(basic_javascript):
    assert len(basic_javascript.imports) == 0

def test_classes(basic_javascript):
    assert len(basic_javascript.classes) == 1

def test_methods(basic_javascript):
    assert len(basic_javascript.methods) == 5

def test_calls(basic_javascript):
    assert len(basic_javascript.calls) == 6

def test_comments(basic_javascript):
    assert len(basic_javascript.comments) == 2
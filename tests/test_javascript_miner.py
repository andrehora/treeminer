from tests.utils import javascript_miner, read_file

class TestBasic:

    @classmethod
    def setup_class(cls):
        cls.miner = javascript_miner(read_file('./tests/samples/basic_javascript.js'))

    def test_imports(self):
        assert len(self.miner.imports) == 0

    def test_classes(self):
        assert len(self.miner.classes) == 1

    def test_methods(self):
        assert len(self.miner.methods) == 5

    def test_calls(self):
        assert len(self.miner.calls) == 6

    def test_comments(self):
        assert len(self.miner.comments) == 2
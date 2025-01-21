from tests.utils import python_miner, fastapi_miner, read_file

class TestBasic:

    @classmethod
    def setup_class(cls):
        cls.miner = python_miner(read_file('./tests/samples/basic_python.py'))

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

class TestExtension:

    @classmethod
    def setup_class(cls):
        cls.miner = fastapi_miner(read_file('./tests/samples/extension_python.py'))

    def test_imports(self):
        assert len(self.miner.imports) == 3

    def test_classes(self):
        assert len(self.miner.classes) == 1

    def test_methods(self):
        assert len(self.miner.methods) == 3

    def test_calls(self):
        assert len(self.miner.calls) == 4

    def test_comments(self):
        assert len(self.miner.comments) == 0

    def test_endpoints(self):
        assert len(self.miner.endpoint_nodes) == 3

        # object, http_method = self.miner.endpoints[0]
        # assert object == 'app'
        # assert http_method == 'get'

        # object, http_method = self.miner.endpoints[1]
        # assert object == 'app'
        # assert http_method == 'get'

        # object, http_method = self.miner.endpoints[2]
        # assert object == 'app'
        # assert http_method == 'put'
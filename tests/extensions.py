from treeminer.miners import PythonMiner

def as_str(text: bytes) -> str:
    return text.decode('utf-8')

class FastAPIMiner(PythonMiner):
    name = 'FastAPI'

    endpoint_objects = ['app', 'router']
    http_methods = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']

    @property    
    def endpoints(self):
        _endpoints = []
        decorators = self.find_nodes_by_type('decorator')
        for decorator in decorators:
            object = self.find_descendant_node_by_field_name(decorator, 'object')
            http_method = self.find_descendant_node_by_field_name(decorator, 'attribute')

            if object and as_str(object.text) in self.endpoint_objects:
                if http_method and as_str(http_method.text) in self.http_methods:
                    data = as_str(object.text), as_str(http_method.text)
                    _endpoints.append(data)

        return _endpoints
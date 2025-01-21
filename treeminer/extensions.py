from treeminer.miners import PythonMiner


def as_str(text: bytes) -> str:
    return text.decode('utf-8')

class FastAPIRepo:

    def __init__(self, endpoints):
        self.endpoints = endpoints

class Endpoint:

    def __init__(self, decorators, function):
        self.decorators = decorators
        self.function = function

class EndpointDecorator:
    
    def __init__(self, object, http_method, arguments):
        self.object = object
        self.http_method = http_method
        self.arguments = arguments

class EndpointFunction:
    
    def __init__(self, name, parameters, return_type, is_async):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
        self.is_async = is_async
    

class FastAPIMiner(PythonMiner):
    name = 'FastAPI'

    fastapi_objects = ['app', 'router']
    http_methods = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']

    @property    
    def endpoints(self):
        result = []
        for endpoint_node in self._endpoint_nodes():
            for node in endpoint_node.children:
                
                # if self._is_fastapi_decorator(node):
                #     endpoint_decorator = self._create_endpoint_decorator(node)
                
                if node.type == 'function_definition':
                    endpoint_function = self._create_endpoint_function(node)
                    result.append(endpoint_function)

        return result
    
    def _create_endpoint_function(self, function_definition):

        is_async = as_str(function_definition.child(0).text) == 'async'
        name = as_str(function_definition.child_by_field_name('name').text)
        
        return_type = ''
        return_type_node = function_definition.child_by_field_name('return_type')
        if return_type_node:
            return_type = as_str(return_type_node.text)

        parameters_node = function_definition.child_by_field_name('parameters')

        if parameters_node:
            params = []
            for param_node in parameters_node.children:
                if param_node.is_named:
                    value = as_str(param_node.children[0].text)
                    type = ''
                    if param_node.type == 'typed_parameter':
                        type = as_str(param_node.child_by_field_name('type').text)
                    if param_node.type == 'typed_default_parameter':
                        type = as_str(param_node.child_by_field_name('type').text)
                        default_value = as_str(param_node.child_by_field_name('value').text)
                    params.append((value, type))
        
        return EndpointFunction(name, params, return_type, is_async)
                    
    
    def _create_endpoint_decorator(self, decorator_node):

        object = as_str(self.find_descendant_node_by_field_name(decorator_node, 'object').text)
        http_method = as_str(self.find_descendant_node_by_field_name(decorator_node, 'attribute').text)
        argumemnts_node = self.find_descendant_node_by_field_name(decorator_node, 'arguments')

        if argumemnts_node:
            args = []
            for arg_node in argumemnts_node.children:
                if arg_node.is_named:
                    if arg_node.type == 'keyword_argument':
                        name = as_str(arg_node.child_by_field_name('name').text)
                        value = as_str(arg_node.child_by_field_name('value').text)
                    else:
                        name = ''
                        value = as_str(arg_node.text)
                    args.append((name, value))
            
        return EndpointDecorator(object, http_method, args)

    def _endpoint_nodes(self):
        result = []
        for node in self.find_nodes_by_type('decorated_definition'):
            if self._is_endpoint(node):
                result.append(node)
        return result
    
    def _is_endpoint(self, decorated_definition_node):
        # Endpoint must have FastAPI decorator (ex: @app.get) and function definition below
        return self._has_function_definition(decorated_definition_node) and self._has_fastapi_decorator(decorated_definition_node)
    
    def _has_function_definition(self, decorated_definition_node):
        return decorated_definition_node.child_by_field_name('definition') is not None
    
    def _has_fastapi_decorator(self, decorated_definition_node):
        for node in decorated_definition_node.children:
            if self._is_fastapi_decorator(node):
                return True
        return False
    
    def _is_fastapi_decorator(self, node):

        if node.type != 'decorator':
            return False

        fastapi_object = self.find_descendant_node_by_field_name(node, 'object')
        http_method = self.find_descendant_node_by_field_name(node, 'attribute')
        
        if fastapi_object and as_str(fastapi_object.text) in self.fastapi_objects:
            if http_method and as_str(http_method.text) in self.http_methods:
                return True
        return False
    
    def fastapi_import(self):
        return self._find_import('FastAPI')

    def apirouter_import(self):
        return self._find_import('APIRouter')
    
    def security_import(self):
        return self._find_import('fastapi.security')
    
    def _find_import(self, entity):
        imports = []
        for imp in self.imports:
            if entity in as_str(imp.text):
                imports.append(as_str(imp.text))
        return imports

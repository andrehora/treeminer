from treeminer.miners import PythonMiner


def as_str(text: bytes) -> str:
    return text.decode('utf-8')

class FastAPIRepo:

    def __init__(self, endpoints):
        self.endpoints = endpoints

class Endpoint:

    def __init__(self, decorator, function):
        self.decorator = decorator
        self.function = function

    def __str__(self):
        return f'{self.decorator} |{" async" if self.function.is_async else ""} {self.function} {f"-> {self.function.return_type}" if self.function.return_type else ""}'

class EndpointDecorator:
    
    def __init__(self, object, http_method, arguments):
        self.object = object
        self.http_method = http_method
        self.arguments = arguments

    def argument_names(self):
        return [arg[0] for arg in self.arguments if arg[0] != '']

    def argument_values(self):
        return [arg[1] for arg in self.arguments]

    def __str__(self):
        return f'{self.http_method} {self.arguments[0][1]}'

class EndpointFunction:
    
    def __init__(self, name, parameters, return_type, is_async):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
        self.is_async = is_async

    def __str__(self):
        return f'{self.name}'
    

class FastAPIMiner(PythonMiner):
    name = 'FastAPI'

    fastapi_objects = ['app', 'router']
    http_methods = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']

    # https://github.com/fastapi/fastapi/blob/master/fastapi/security/__init__.py
    security_classes = ['APIKeyCookie', 'APIKeyHeader', 'APIKeyQuery', 'HTTPAuthorizationCredentials', 
                        'HTTPBasic', 'HTTPBasicCredentials', 'HTTPBearer', 'HTTPDigest', 'OAuth2',
                        'OAuth2AuthorizationCodeBearer', 'OAuth2PasswordBearer', 'OAuth2PasswordRequestForm',
                        'OAuth2PasswordRequestFormStrict', 'SecurityScopes', 'OpenIdConnect']

    @property    
    def endpoints(self):

        result = []

        for decorated_definition_node in self.find_nodes_by_type('decorated_definition'):
            for node in decorated_definition_node.children:

                if self._is_fastapi_decorator(node):
                    endpoint_decorator = self._create_endpoint_decorator(node)
                    endpoint_function = None
                    
                    function_definition_node = decorated_definition_node.child_by_field_name('definition')
                    if function_definition_node:
                        endpoint_function = self._create_endpoint_function(function_definition_node)

                    if endpoint_decorator and endpoint_function:
                        endpoint = Endpoint(endpoint_decorator, endpoint_function)
                        result.append(endpoint)

        return result
    
    def _create_endpoint_decorator(self, decorator_node):

        object = as_str(self.descendant_node_by_field_name(decorator_node, 'object').text)
        http_method = as_str(self.descendant_node_by_field_name(decorator_node, 'attribute').text)
        argumemnts_node = self.descendant_node_by_field_name(decorator_node, 'arguments')

        if argumemnts_node:
            args = []
            for arg_node in self.named_children(argumemnts_node):

                if arg_node.type == 'keyword_argument':
                    name = as_str(arg_node.child_by_field_name('name').text)
                    value = as_str(arg_node.child_by_field_name('value').text)
                else:
                    name = ''
                    value = as_str(arg_node.text)
                args.append((name, value))
            
        return EndpointDecorator(object, http_method, args)
    
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
            for param_node in self.named_children(parameters_node):
                
                param_name = None
                param_type = None

                if param_node.type == 'identifier':
                    param_name = as_str(param_node.text)    
                
                if param_node.type == 'typed_parameter':
                    param_name = as_str(param_node.children[0].text)
                    param_type = as_str(param_node.child_by_field_name('type').text)
                
                if param_node.type == 'typed_default_parameter':
                    param_type = as_str(param_node.child_by_field_name('type').text)
                    param_default_value = as_str(param_node.child_by_field_name('value').text)

                params.append((param_name, param_type))
        
        return EndpointFunction(name, params, return_type, is_async)
    
    def _is_fastapi_decorator(self, node):

        if node.type != 'decorator':
            return False

        decorator_obj = self.descendant_node_by_field_name(node, 'object')
        decorator_att = self.descendant_node_by_field_name(node, 'attribute')
        
        if decorator_obj:
            for fastapi_obj in self.fastapi_objects:
                if fastapi_obj in as_str(decorator_obj.text):
                    if decorator_att and as_str(decorator_att.text) in self.http_methods:
                        return True
        return False
    
    def fastapi_imports(self):
        return self._find_import('FastAPI')

    def apirouter_imports(self):
        return self._find_import('APIRouter')
    
    def security_imports(self):
        imports = []
        for imp in self.imports:
            for imp_element in imp.children_by_field_name('name'):
                for security_class in self.security_classes:
                    if security_class == as_str(imp_element.text):
                        imports.append(security_class)
        return imports
    
    def _find_import(self, entity):
        imports = []
        for imp in self.imports:
            if entity in as_str(imp.text):
                imports.append(as_str(imp.text))
        return imports

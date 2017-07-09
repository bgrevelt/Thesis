import json
class configuration:
    def __init__(self, path = 'configuration/config.cfg'):
        self.decoded = json.loads(open(path).read())
        self.validate_decoded()
        self.algorithms = {d['name'] : d for d in self.decoded['algorithms']}

    def get_input_files(self):
        return self.decoded['input files']

    def get_algorithms(self):
        return self.algorithms.keys()

    def get_algorithm_module_path(self, algorithm):
        if algorithm not in self.algorithms:
            raise ValueError

        return self.algorithms[algorithm]['path']

    def get_algorithm_parameters(self, algorithm):
        if algorithm not in self.algorithms:
            raise ValueError

        if 'parameters' not in self.algorithms[algorithm]:
            return ''
        else:
            return json.dumps(self.algorithms[algorithm]['parameters'])

    def validate_decoded(self):
        required_fields = [
            ('input files', 1, 'Congiguration file does not contain any input files'),
            ('algorithms', 1, 'Congiguration file does not contain any algorithms to test')
            #TODO:
            #('metric parameters.acquisition cpu available', 1, 'Congiguration file does not contain anvailable CPU for acquisition metric')
            #('metric parameters.acquisition memory available', 1, 'Congiguration file does not contain available memory for acquisition metric')

        ]

        for field, min_size, msg in required_fields:
            if field not in self.decoded:
                raise ValueError('Field {} missing from congiguration file'.format(field))
            if min_size > 0 and len(self.decoded[field]) < min_size:
                raise ValueError(msg)

    def get_metric_parameters(self, param=None):
        if not param:
            return self.decoded['metric parameters']
        elif param not in self.decoded['metric parameters']:
            print(self.decoded)
            raise ValueError('Request for metric parameter "{}" that is not part of configuration file'.format(param))
        else:
            return self.decoded['metric parameters'][param]



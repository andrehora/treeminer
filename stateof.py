import statistics

from datetime import date, datetime
from numbers import Number
from collections import Counter

from tree_sitter import Node
from treeminer.repo import Repo, Commit


def as_str(text: bytes) -> str:
    return text.decode('utf-8')

def aggregate_basic(values: list[Number], measure: str) -> Number:
    if measure == 'max':
        return max(values)
    if measure == 'min':
        return min(values)
    return sum(values)

def aggregate_stat(values: list[Number], measure: str) -> Number:
    operation = getattr(statistics, measure)
    result = operation(values)
    return round(result, 2)

class DateUtil:

    date_unit: str = 'year'
    MONTH = 12
    DAY = 1
    
    @classmethod
    def dates_by_unit(cls, start_date: date, end_date: date) -> list[date]:
        assert end_date >= start_date
        dates = []
        if cls.date_unit == 'year':
            dates = cls._generate_years(start_date, end_date)
        if cls.date_unit == 'month':
            dates = cls._generate_months(start_date, end_date)
        return dates
    
    @classmethod
    def formatted_dates(cls, dates: list[date]) -> list[str]:
        if cls.date_unit == 'year':
            return [each.strftime('%Y') for each in dates]
        if cls.date_unit == 'month':
            return [each.strftime('%m/%Y') for each in dates]
    
    @classmethod
    def _generate_years(cls, start_date: date, end_date: date) -> list[date]:
        dates = list(range(start_date.year, end_date.year+1))
        return [date(year, cls.MONTH, 1) for year in dates]

    @classmethod
    def _generate_months(cls, start_date: date, end_date: date) -> list[date]:
        start_month = start_date.month
        start_year = start_date.year
        end_month = end_date.month
        end_year = end_date.year

        if start_year == end_year:
            dates = [(month, start_year) for month in range(start_month, end_month + 1)]
            return cls._convert_tuples_to_dates(dates)

        start_year_months = [(month, start_year) for month in range(start_month, 13)]
        middle_years_months = [(month, year) for year in range(start_year + 1, end_year) for month in range(1, 13)]
        end_year_months = [(month, end_year) for month in range(1, end_month + 1)]

        return cls._convert_tuples_to_dates(start_year_months + middle_years_months + end_year_months)

    @classmethod
    def _convert_tuples_to_dates(cls, dates: list[tuple[int,int]]) -> list[date]:
        return [date(year, month, 1) for month, year in dates]

class MetricInfo:
    
    def __init__(self, name: str, callback, file_extension: str, 
                 include_named_nodes: bool, include_unnamed_nodes: bool,
                 categorical: bool, aggregate: str):
        
        self._name = name
        self.callback = callback
        self.file_extension = file_extension
        self.include_named_nodes = include_named_nodes
        self.include_unnamed_nodes = include_unnamed_nodes
        self.categorical = categorical
        self.aggregate = aggregate

    @property
    def name(self):
        if self._name is None:
            return self.callback.__name__
        return self._name
    
class ParsedFile:

    def __init__(self, name: str, path: str, nodes: list[Node]):
        self.name = name
        self.path = path
        self.nodes = nodes

class ParsedCommit:
    
    def __init__(self, hash: str, date: datetime, parsed_files: list[ParsedFile]):
        self.hash = hash
        self.date = date
        self.parsed_files = parsed_files

    @property
    def nodes(self) -> list[Node]:
        return [node for file in self.parsed_files for node in file.nodes]
    
    def node_types(self, node_types: list[str] = None) -> list[str]:
        if node_types is None:
            return [node.type for node in self.nodes]
        return [node.type for node in self.nodes if node.type in node_types]
    
    def count_nodes(self, node_types: list[str] = None) -> int:
        if node_types is None:
            return len(self.nodes)
        return len(self._find_nodes_by_type(node_types))
    
    def loc(self, node_type: str, measure: str = 'median') -> Number:

        if measure not in ['median', 'mean', 'mode']:
            raise BadLOCMeasure(f'LOC measure should be median, mean, or mode')
        
        nodes = self._find_nodes_by_type([node_type])
        locs = [len(as_str(node.text).split('\n')) for node in nodes]
        
        return aggregate_stat(locs, measure)
    
    def _find_nodes_by_type(self, node_types: list[str]) -> list[Node]:
        return [node for node in self.nodes if node.type in node_types]

class MetricEvolution:

    def __init__(self, name: str, dates: list[str], values: list[Number]):
        self.name = name
        self.dates = dates
        self.values = values
    
    @property
    def dates_and_values(self):
        return list(zip(self.dates, self.values))
    
    def __str__(self):
        return f'{self.name} {self.dates} {str(self.values)}'
    
class MetricResult:

    def __init__(self, name: str, value: Number, date: date):
        self.name = name
        self.value = value
        self.date = date

class CommitResult:

    def __init__(self, hash: str, date: date):
        self.hash = hash
        self.date = date
        self.metric_results: list[MetricResult] = []

    def add_metric_result(self, metric_result: MetricResult):
        self.metric_results.append(metric_result)

class ProjectResult:

    def __init__(self, name: str):
        self.name = name
        self.commit_results: list[CommitResult] = []

    def add_commit_result(self, commit_result: CommitResult):
        self.commit_results.append(commit_result)

    def metric_evolution(self, metric_name: str) -> MetricEvolution:    
        date_steps = self.date_steps()
        values = []
        
        metric_results = sorted(self._metric_results(metric_name), key=lambda each: each.date, reverse=True)
        for date_step in date_steps:
            found_date = False
            for metric_result in metric_results:
                real_date = date(metric_result.date.year, metric_result.date.month, 1)
                if date_step >= real_date:
                    values.append(metric_result.value)
                    found_date = True
                    break
            # Fill the missing metric values, which may happen in categorical metrics
            if not found_date:
                values.append(0)
        
        assert len(date_steps) == len(values), f'{len(date_steps)} != {len(values)}'

        date_steps = DateUtil.formatted_dates(date_steps)
        return MetricEvolution(metric_name, date_steps, values)
    
    def date_steps(self) -> list[date]:
        first_commit_date = self.commit_results[0].date
        today_date = date.today()
        return DateUtil.dates_by_unit(first_commit_date, today_date)
    
    def _metric_results(self, metric_name: str) -> list[MetricResult]:
        metric_results = []
        for commit_result in self.commit_results:
            for metric_result in commit_result.metric_results:
                if metric_result.name == metric_name:
                    metric_results.append(metric_result)
        return metric_results

class Result:

    def __init__(self, date_unit: str):
        DateUtil.date_unit = date_unit
        self.project_results: list[ProjectResult] = []
        self.metrics = MetricsAggregatorInfo()

    @property
    def metric_names(self) -> list[str]:
        return self.metrics.names
    
    def add_metric(self, name: str, aggregate: str):
        self.metrics.add(name, aggregate)

    def add_project_result(self, project_result: ProjectResult):
        self.project_results.append(project_result)

    def date_steps(self) -> list[date]:
        dates = set()
        for project_result in result.project_results:
            project_dates = project_result.date_steps()
            dates.update(project_dates)
        return sorted(list(dates))
    
    def evolutions(self) -> list[MetricEvolution]:
        metric_evolutions = []
        for metric_name, metric_agg in self.metrics.names_and_aggregates:
            metric_evo = self.metric_evolution(metric_name, metric_agg)
            metric_evolutions.append(metric_evo)
        return metric_evolutions

    def metric_evolution(self, metric_name: str, aggregate: str) -> MetricEvolution:

        dates = DateUtil.formatted_dates(self.date_steps())

        # If one project, just return its dates and values
        if len(self.project_results) == 1:
            project = self.project_results[0]
            values = project.metric_evolution(metric_name).values
            return MetricEvolution(metric_name, dates, values)

        # If multiples projects, we need to aggregate the values...

        values_by_date = {date: [] for date in dates}

        for project_result in self.project_results:
            metric_evolution = project_result.metric_evolution(metric_name)
            for date, value in metric_evolution.dates_and_values:
                values_by_date[date].append(value)
        
        # Aggregate values
        values = []
        for metric_values in values_by_date.values():
            
            value = None
            if aggregate in ['sum', 'max', 'min']:
                value = aggregate_basic(metric_values, aggregate)
            if aggregate in ['median', 'mean', 'mode']:
                value = aggregate_stat(metric_values, aggregate)
            
            assert value is not None
            values.append(value)

        return MetricEvolution(metric_name, dates, values)
    
    def summary(self):
        for evo in self.evolutions():
            print(evo)

class MetricsAggregatorInfo:

    def __init__(self):
        self.data: dict[str, str] = {}

    @property
    def names(self) -> list[str]:
        return list(self._metrics.keys())
    
    @property
    def names_and_aggregates(self):
        return self.data.items()

    def add(self, name: str, aggregate: str):
        if name in self.data:
            return
        self.data[name] = aggregate
                
class GitEvo:

    def __init__(self, projects: list[str], file_extension: str | None = None, 
                 date_unit: str = 'year', since_year: int | None = None):
        
        if date_unit not in ['year', 'month']:
            raise BadDateUnit('date_unit must be year or month')

        self.projects = projects
        self.global_file_extension = None
        if file_extension is not None:
            self.global_file_extension = file_extension
        self.date_unit = date_unit
        self.since_year = since_year

        self.registered_metrics: list[MetricInfo] = []
        self.analyzed_commits: list[str] = []
        self._repo = Repo(self.projects)

    def metric(self, name: str = None,
               *,
               file_extension: str | None = None, 
               include_named_nodes: bool = True, 
               include_unnamed_nodes: bool = False, 
               categorical: bool = False, 
               aggregate: str = 'sum'):
        
        def decorator(func):
            self.registered_metrics.append(
                MetricInfo(name=name, 
                           callback=func,
                           file_extension=file_extension,
                           include_named_nodes=include_named_nodes,
                           include_unnamed_nodes=include_unnamed_nodes,
                           categorical=categorical,
                           aggregate=aggregate))
            return func
        return decorator
    
    def compute(self) -> Result:
        
        # Sanity checks on registered_metrics
        result = Result(self.date_unit)
        for metric_info in self.registered_metrics:

            if self.global_file_extension is None and metric_info.file_extension is None:
                raise FileExtensionNotFound(f'file_extension should be defined in metric {metric_info.name}')
            
            if metric_info.aggregate not in ['median', 'mean', 'mode', 'sum', 'max', 'min']:
                raise BadAggregate(f'aggregate in metric {metric_info.name} should be median, mean, mode, sum, max, or min')

            if not metric_info.categorical:
                result.add_metric(metric_info.name, metric_info.aggregate)

        project_result = None
        project_name = ''
        project_commits = set()
        for commit in self._repo.commits:

            # Create new project result if new project name
            if project_name != commit.project_name:
                project_name = commit.project_name
                project_commits = set()
                project_result = ProjectResult(commit.project_name)
                result.add_project_result(project_result)
            
            # Skip commit based on since_year
            if self.since_year and commit.committer_date.year < self.since_year:
                continue
            
            # Skip commit if year or month is already analyzed
            commit_year = commit.committer_date.year
            selected_date = (commit_year, commit.committer_date.month) if self.date_unit == 'month' else commit_year
            if selected_date in project_commits:
                continue
            project_commits.add(selected_date)

            # Iterate on each metric
            commit_result = CommitResult(commit.hash, commit.committer_date.date())
            for metric_info in self.registered_metrics:
                
                # Create parsed commit
                parsed_commit = self._create_parsed_commit(commit, metric_info)
                
                # Run the metric callback
                metric_value = metric_info.callback(parsed_commit)
                metric_name = metric_info.name

                # Process categorical metrics
                if metric_info.categorical: 

                    if not isinstance(metric_value, list):
                        raise BadReturnType(f'categorical metric {metric_info.name} should return list of strings')

                    for name, value in Counter(metric_value).most_common():
                        assert isinstance(name, str), f'categorical metric {metric_info.name} should return list of strings'
                        metric_result = MetricResult(name=name, value=value, date=commit_result.date)
                        commit_result.add_metric_result(metric_result)
                        result.add_metric(name, metric_info.aggregate)
                
                # Process Numerical metrics
                else:
                    
                    if not isinstance(metric_value, (int, float)):
                        raise BadReturnType(f'numerical metric {metric_info.name} should return int or float')

                    metric_result = MetricResult(name=metric_name, value=metric_value, date=commit_result.date)
                    commit_result.add_metric_result(metric_result)
        
            project_result.add_commit_result(commit_result)
        
        return result

    def _create_parsed_commit(self, commit: Commit, metric_info: MetricInfo) -> ParsedCommit:
        parsed_files = []

        file_extension = metric_info.file_extension
        named_nodes = metric_info.include_named_nodes
        unnamed_nodes = metric_info.include_unnamed_nodes

        if file_extension is not None: target_extension = file_extension
        else: target_extension = self.global_file_extension

        for file in commit.all_files([target_extension]):
            
            file_nodes = []
            if named_nodes and unnamed_nodes: file_nodes = [node for node in file.tree_nodes]
            elif named_nodes: file_nodes = [node for node in file.tree_nodes if node.is_named]
            elif unnamed_nodes: file_nodes = [node for node in file.tree_nodes if not node.is_named]

            parsed_file = ParsedFile(file.filename, file.path, file_nodes)
            parsed_files.append(parsed_file)

        return ParsedCommit(commit.hash, commit.committer_date, parsed_files)
    
class FileExtensionNotFound(Exception):
    pass

class BadAggregate(Exception):
    pass

class BadReturnType(Exception):
    pass

class BadDateUnit(Exception):
    pass

class BadLOCMeasure(Exception):
    pass

# projects = ['git/FastAPI-template']
projects = ['git/full-stack-fastapi-template']
# projects = ['git/dispatch']
# projects = ['git/fastapi']
# projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template']
projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template', 'git/dispatch', 'git/fastapi']


evo = GitEvo(projects=projects, file_extension='.py', date_unit='year')

# @evo.metric('python_files', aggregate='sum')
# def python_files(commit: ParsedCommit):
#     return len(commit.parsed_files)

# @evo.metric('test_files', aggregate='sum')
# def test_files(commit: ParsedCommit):
#     return len([file.name for file in commit.parsed_files if 'test' in file.path])

# @evo.metric('nodes', categorical=True, aggregate='sum')
# def unnamed_nodes(commit: ParsedCommit):
#     return commit.node_types()

@evo.metric(name='imports', categorical=True)
def imports(commit: ParsedCommit):
    return commit.node_types(['import_statement', 'import_from_statement', 'future_import_statement'])

# @evo.metric(name='all_imports')
# def all_imports(commit: ParsedCommit):
#     import_nodes = ['import_statement', 'import_from_statement', 'future_import_statement']
#     return commit.count_nodes(import_nodes)

# @evo.metric(name='import_from_statement')
# def import_from_statement(commit: ParsedCommit):
#     return commit.count_nodes(['import_from_statement'])

# @evo.metric(name='import_statement')
# def import_statement(commit: ParsedCommit):
#     return commit.count_nodes(['import_statement'])

# @evo.metric(name='future_import_statement')
# def future_import_statement(commit: ParsedCommit):
#     return commit.count_nodes(['future_import_statement'])

# @evo.metric(name='class_definition', aggregate='sum')
# def decorated(commit: ParsedCommit):
#     return commit.count_nodes(['class_definition'])

# @evo.metric(name='function_definition', aggregate='sum')
# def decorated(commit: ParsedCommit):
#     return commit.count_nodes(['function_definition'])

# @evo.metric(name='decorated')
# def decorated(commit: ParsedCommit):
#     return commit.count_nodes(['decorated_definition'])

# @evo.metric(name='classes (LOC)')
# def classes(commit: ParsedCommit):
#     return commit.loc('class_definition', 'median')

# @evo.metric('functions (LOC)')
# def functions(commit: ParsedCommit):
#     return commit.loc('function_definition', 'mean')

result = evo.compute()
result.summary()

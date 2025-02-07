import statistics

from datetime import date, datetime
from numbers import Number
from collections import Counter

from tree_sitter import Node
from treeminer.repo import Repo, Commit


def as_str(text: bytes) -> str:
    return text.decode('utf-8')

class DateUtil:

    date_unit: str = 'year'
    MONTH = 12
    DAY = 1
    
    @classmethod
    def dates_by_unit(cls, start_date: date, end_date: date) -> list[date]:
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
    
    def __init__(self, name: str, callback, categorical: bool, all_nodes: bool):
        self._name = name
        self.callback = callback
        self.categorical = categorical
        self.all_nodes = all_nodes

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
        assert measure in ['median', 'mean', 'mode'], 'measure should be mean, median, or mode'
        
        nodes = self._find_nodes_by_type([node_type])
        locs = [len(as_str(node.text).split('\n')) for node in nodes]
        operation = getattr(statistics, measure)
        return operation(locs)
    
    def _find_nodes_by_type(self, node_types: list[str]) -> list[Node]:
        return [node for node in self.nodes if node.type in node_types]

class MetricEvolution:

    def __init__(self, name: str, dates: list[str], values: list[Number]):
        self.name = name
        self.dates = dates
        self.values = values
    
    @property
    def values_as_str(self) -> list[str]:
        return [str(each) for each in self.values]
    
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
        self._metric_names: list[str] = []

    @property
    def metric_names(self) -> set[str]:
        return list(dict.fromkeys(self._metric_names))

    def add_project_result(self, project_result: ProjectResult):
        self.project_results.append(project_result)

    def add_metric_name(self, name: str):
        self._metric_names.append(name)

    def date_steps(self) -> list[date]:
        dates = set()
        for project_result in result.project_results:
            project_dates = project_result.date_steps()
            dates.update(project_dates)
        return sorted(list(dates))

    def metric_evolution(self, metric_name: str, measure: str = 'median') -> MetricEvolution:

        dates = DateUtil.formatted_dates(self.date_steps())

        values_by_date = {}
        for date in dates:
            values_by_date[date] = []

        for project_result in self.project_results:
            metric_evolution = project_result.metric_evolution(metric_name)
            for date, value in metric_evolution.dates_and_values:
                values_by_date[date].append(value)
        
        values = []
        for metric_values in values_by_date.values():
            operation = getattr(statistics, measure)
            result = operation(metric_values)
            values.append(round(result, 2))

        return MetricEvolution(metric_name, dates, values)
                

class EvoGit:

    def __init__(self, name: str, projects: list[str], file_extensions: list[str] | None, 
                 date_unit: str = 'year', since_year: int | None = None):
        
        assert date_unit in ['year', 'month'], 'date_unit must be year or month'

        self.name = name
        self.projects = projects
        self.file_extensions = file_extensions
        self.date_unit = date_unit
        self.since_year = since_year

        self.registered_metrics: list[MetricInfo] = []
        self.analyzed_commits: list[str] = []
        self._repo = Repo(self.projects)

    def metric(self, name: str = None, categorical: bool = False, all_nodes: bool = False):
        def decorator(func):
            self.registered_metrics.append(
                MetricInfo(name=name, callback=func, categorical=categorical, 
                           all_nodes=all_nodes))
            return func
        return decorator
    
    def compute_metrics(self) -> Result:
        
        result = Result(self.date_unit)
        for metric_info in self.registered_metrics:
            if not metric_info.categorical:
                result.add_metric_name(metric_info.name)

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
                parsed_commit = self._create_parsed_commit(commit, metric_info.all_nodes)
                
                # Run the metric callback
                metric_value = metric_info.callback(parsed_commit)
                metric_name = metric_info.name

                # Process the metric return value
                if metric_info.categorical:
                    assert isinstance(metric_value, list), 'categorical metric should return list of strings'
                    for name, value in Counter(metric_value).most_common():
                        metric_result = MetricResult(name=name, value=value, date=commit_result.date)
                        commit_result.add_metric_result(metric_result)
                        result.add_metric_name(name)
                else:
                    assert isinstance(metric_value, (int, float)), 'numerical metrics should return int or float'
                    metric_result = MetricResult(name=metric_name, value=metric_value, date=commit_result.date)
                    commit_result.add_metric_result(metric_result)
        
            project_result.add_commit_result(commit_result)
        
        return result

    def _create_parsed_commit(self, commit: Commit, all_nodes: bool) -> ParsedCommit:
        
        parsed_files = []
        for file in commit.all_files(self.file_extensions):

            if all_nodes: file_nodes = [node for node in file.tree_nodes]
            else: file_nodes = [node for node in file.tree_nodes if node.is_named]

            parsed_file = ParsedFile(file.filename, file.path, file_nodes)
            parsed_files.append(parsed_file)

        return ParsedCommit(commit.hash, commit.committer_date, parsed_files)

# projects = ['git/FastAPI-template']
projects = ['git/full-stack-fastapi-template']
# projects = ['git/dispatch']
# projects = ['git/fastapi']
# projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template']
# projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template', 'git/dispatch', 'git/fastapi']

app = EvoGit('Foo', projects=projects, file_extensions=['.py'], date_unit='year')

@app.metric(name='named_nodes')
def named_nodes(commit: ParsedCommit):
    return commit.count_nodes()

@app.metric(name='all_nodes', all_nodes=True)
def all_nodes(commit: ParsedCommit):
    return commit.count_nodes()

# @app.metric(name='imports', categorical=True)
# def imports(nodes: Nodes):
#     return nodes.node_types(['import_statement', 'import_from_statement', 'future_import_statement'])

# @app.metric(name='all_imports')
# def all_imports(nodes: Nodes):
#     import_nodes = ['import_statement', 'import_from_statement', 'future_import_statement']
#     return nodes.count_nodes(import_nodes)

# @app.metric(name='all_imports')
# def all_imports(nodes: Nodes):
#     import_nodes = ['import_statement', 'import_from_statement', 'future_import_statement']
#     return nodes.count_nodes(import_nodes)

# @app.metric(name='import_from_statement')
# def import_from_statement(nodes: Nodes):
#     return nodes.count_nodes(['import_from_statement'])

# @app.metric(name='import_statement')
# def import_statement(nodes: Nodes):
#     return nodes.count_nodes(['import_statement'])

# @app.metric(name='future_import_statement')
# def future_import_statement(nodes: Nodes):
#     return nodes.count_nodes(['future_import_statement'])

# @app.metric(name='decorated')
# def decorated(nodes: Nodes):
#     return nodes.count_nodes(['decorated_definition'])

# @app.metric(name='classes (LOC)')
# def classes(nodes: Nodes):
#     return nodes.loc('class_definition', 'median')

# @app.metric('functions (LOC)')
# def functions(nodes: Nodes):
#     return nodes.loc('function_definition', 'median')

result = app.compute_metrics()
for metric_name in result.metric_names:
    values = result.metric_evolution(metric_name)
    print(values)
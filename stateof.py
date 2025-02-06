import statistics

from datetime import date
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
    
    def __init__(self, name: str, categorical: bool, callback):
        self._name = name
        self.categorical = categorical
        self.callback = callback

    @property
    def name(self):
        if self._name is None:
            return self.callback.__name__
        return self._name

class Nodes:
    
    def __init__(self, nodes: list[Node]):
        self.nodes = nodes

    @property
    def size(self):
        return len(self.nodes)
    
    def by_types(self, node_types: list[str] = None) -> list[str]:
        if node_types is None:
            return [node.type for node in self.nodes]
        return [node.type for node in self.nodes if node.type in node_types]
    
    def find_by_type(self, node_types: list[str]) -> list[Node]:
        return [node for node in self.nodes if node.type in node_types]
    
    def count_by_type(self, node_types: list[str]) -> int:
        return len(self.find_by_type(node_types))
    
    def loc_by_type(self, node_types: list[str], measure: str = 'median') -> Number | list[Number]:
        nodes = self.find_by_type(node_types)
        locs = [len(as_str(node.text).split('\n')) for node in nodes]
        operation = getattr(statistics, measure)
        return operation(locs)

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
                

class StateOf:

    def __init__(self, name: str, projects: list[str], file_extensions: list[str] | None, 
                 date_unit: str = 'year', since_year: int | None = None):
        
        assert date_unit in ['year', 'month'], 'date_unit must be "year" or "month"'

        self.name = name
        self.projects = projects
        self.file_extensions = file_extensions
        self.date_unit = date_unit
        self.since_year = since_year

        self.registered_metrics: list[MetricInfo] = []
        self.analyzed_commits: list[str] = []
        self._repo = Repo(self.projects)

    def metric(self, name: str = None, categorical: bool = False):
        def decorator(func):
            self.registered_metrics.append(
                MetricInfo(name=name, categorical=categorical, callback=func))
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

            # Compute the metrics for the commit nodes
            commit_result = CommitResult(commit.hash, commit.committer_date.date())
            for metric_info in self.registered_metrics:
                
                commit_nodes = self._get_all_nodes(commit)
                node_list = Nodes(commit_nodes)
                
                # Run the callback metrics
                metric_value = metric_info.callback(node_list)
                metric_name = metric_info.name

                # Process the metric value
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

    def _get_all_nodes(self, commit: Commit):
        _commit_nodes = []
        for file in commit.all_files(self.file_extensions):
            file_nodes = list(file.tree_nodes)
            _commit_nodes.extend(file_nodes)
        return _commit_nodes

# projects = ['git/FastAPI-template']
# projects = ['git/full-stack-fastapi-template']
# projects = ['git/dispatch']
# projects = ['git/fastapi']
# projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template']
projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template', 'git/dispatch', 'git/fastapi']

app = StateOf('Foo', projects=projects, file_extensions=['.py'], date_unit='year')

@app.metric(name='types', categorical=True)
def all_types(nodes: Nodes):
    # return nodes.by_types()
    return nodes.by_types(['import_statement', 'import_from_statement', 'future_import_statement'])

# @app.metric(name='all_imports')
# def all_imports(nodes: Nodes):
#     import_nodes = ['import_statement', 'import_from_statement', 'future_import_statement']
#     return nodes.count_by_type(import_nodes)

# @app.metric(name='all_imports')
# def all_imports(nodes: Nodes):
#     import_nodes = ['import_statement', 'import_from_statement', 'future_import_statement']
#     return nodes.count_by_type(import_nodes)

# @app.metric(name='import_from_statement')
# def import_from_statement(nodes: Nodes):
#     return nodes.count_by_type(['import_from_statement'])

# @app.metric(name='import_statement')
# def import_statement(nodes: Nodes):
#     return nodes.count_by_type(['import_statement'])

# @app.metric(name='future_import_statement')
# def future_import_statement(nodes: Nodes):
#     return nodes.count_by_type(['future_import_statement'])

# @app.metric(name='decorated')
# def decorated(nodes: Nodes):
#     return nodes.count_by_type(['decorated_definition'])

# @app.metric(name='classes (LOC)')
# def classes(nodes: Nodes):
#     return nodes.loc_by_type(['class_definition'])

# @app.metric('functions')
# def functions(nodes: Nodes):
#     return nodes.loc_by_type(['function_definition'], 'median')

result = app.compute_metrics()
for metric_name in result.metric_names:
    values = result.metric_evolution(metric_name)
    print(values)
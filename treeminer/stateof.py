import statistics

from datetime import datetime, date
from collections import Counter
from numbers import Number

from tree_sitter import Node
from treeminer.repo import Repo, Commit
from extensions import FastAPIMiner


def as_str(text: bytes) -> str:
    return text.decode('utf-8')


class MetricInfo:
    
    def __init__(self, name, callback):
        self._name = name
        self.callback = callback

    @property
    def name(self):
        if self._name is None:
            return self.callback.__name__
        return self._name

class NodeList:
    
    def __init__(self, nodes: list[Node]):
        self.nodes = nodes

    @property
    def size(self):
        return len(self.nodes)
    
    def count_types(self, node_types: list[str]) -> int:
        return len(self.find_types(node_types))
    
    def find_types(self, node_types: list[str]) -> list[Node]:
        nodes = []
        for node in self.nodes:
            if node.type in node_types:
                nodes.append(node)
        return nodes
    
    def loc_for_types(self, node_types: list[str], stat: str = 'median') -> Number | list[Number]:
        nodes = self.find_types(node_types)
        locs = [len(as_str(node.text).split('\n')) for node in nodes]
        operation = getattr(statistics, stat)
        return operation(locs)
    

class MetricResult:

    def __init__(self, name: str, value: Number, datetime: datetime):
        self.name = name
        self.value = value
        self.datetime = datetime

class CommitResult:

    def __init__(self, hash: str, datetime: datetime):
        self.hash = hash
        self.datetime = datetime
        self.metric_results: list[MetricResult] = []

    def add_metric_result(self, metric_result: MetricResult):
        self.metric_results.append(metric_result)

class ProjectResult:

    def __init__(self, name: str):
        self.name = name
        self.commit_results: list[CommitResult] = []

    def add_commit_result(self, commit_result: CommitResult):
        self.commit_results.append(commit_result)

    def commit_dates(self):
        return [commit_result.datetime.strftime('%m/%Y') for commit_result in self.commit_results]

    def metric_values(self, metric_name: str):
        return [str(metric_result.value) for metric_result in self._metric_results(metric_name)]

    def metric_values_with_missing_dates(self, metric_name: str, date_unit: str = 'year'):

        start_date = self.commit_results[0].datetime
        end_date = self.commit_results[-1].datetime
        all_dates = self._generate_years(start_date, end_date)

        all_dates = []
        if date_unit == 'year':
            all_dates = self._generate_years(start_date, end_date)
        if date_unit == 'month':
            all_dates = self._generate_months(start_date, end_date)

        values = []
        metric_results = sorted(self._metric_results(metric_name), key=lambda each: each.datetime, reverse=True)
        for date in all_dates:
            for metric_result in metric_results:
                if self._ge(date, metric_result.datetime, date_unit):
                    values.append(str(metric_result.value))
                    break
        return self._pretty_dates(all_dates, date_unit), values
    
    def _pretty_dates(self, dates: list[datetime], date_unit) -> list[str]:
        if date_unit == 'year':
            return [date.strftime('%Y') for date in dates]
        if date_unit == 'month':
            return [date.strftime('%m/%Y') for date in dates]
    
    def _ge(self, date1: datetime, date2: datetime, date_unit: str):
        if date_unit == 'year':
            return date1.year >= date2.year
        if date_unit == 'month':
            return date1.year >= date2.year and date1.month >= date2.month

    def _metric_results(self, metric_name: str) -> list[MetricResult]:
        values = []
        for commit_result in self.commit_results:
            for metric_result in commit_result.metric_results:
                if metric_result.name == metric_name:
                    values.append(metric_result)
        return values

    def _generate_years(self, start_date: datetime, end_date: datetime) -> list[date]:
        dates = list(range(start_date.year, end_date.year+1))
        return [date(year, 1, 1) for year in dates]
    
    def _generate_months(self, start_date: datetime, end_date: datetime) -> list[date]:
        start_month = start_date.month
        start_year = start_date.year
        end_month = end_date.month
        end_year = end_date.year

        if start_year == end_year:
            dates = [(month, start_year) for month in range(start_month, end_month + 1)]
            return self._to_date(dates)

        start_year_months = [(month, start_year) for month in range(start_month, 13)]
        middle_years_months = [(month, year) for year in range(start_year + 1, end_year) for month in range(1, 13)]
        end_year_months = [(month, end_year) for month in range(1, end_month + 1)]

        return self._to_date(start_year_months + middle_years_months + end_year_months)
    
    def _to_date(self, dates: list[tuple[int,int]]) -> list[date]:
        return [date(year, month, 1) for month, year in dates]

class Result:

    def __init__(self):
        self.project_results: list[ProjectResult] = []
        self.metric_names: list[str] = []

    def add_project_result(self, project_result: ProjectResult):
        self.project_results.append(project_result)

    def add_metric_name(self, name):
        self.metric_names.append(name)


class StateOf:

    def __init__(self, name: str, commit_selection: str = 'year'):

        self.name = name
        self.file_extensions: list[str] = []
        self.projects: list[str] = []
        self.registered_metrics: list[MetricInfo] = []
        self.analyzed_commits: list[str] = []
        self.commit_selection = commit_selection

        only_releases = False
        if commit_selection == 'release':
            only_releases = True
        self._repo = Repo(projects, only_releases=only_releases)

    def metric(self, name: str = None):
        def decorator(func):
            self.registered_metrics.append(
                MetricInfo(name=name, callback=func))
            return func
        return decorator
    
    def compute_metrics(self) -> Result:
        
        result = Result()
        for metric_info in self.registered_metrics:
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
            
            # Check commit selection
            if self.commit_selection in ['year', 'month']:
                commit_year = commit.committer_date.year
                selected_date = (commit_year, commit.committer_date.month) if self.commit_selection == 'month' else commit_year
                # Skip commit if selected_date is already analyzed
                if selected_date in project_commits:
                    continue
                project_commits.add(selected_date)

            # Compute the metrics for the commit nodes
            commit_result = CommitResult(commit.hash, commit.committer_date)
            for metric_info in self.registered_metrics:
                
                commit_nodes = self._get_all_nodes(commit)
                node_list = NodeList(commit_nodes)
                
                # Compute the metric value
                metric_value = metric_info.callback(node_list)
                metric_name = metric_info.name
                
                metric_result = MetricResult(name=metric_name, value=metric_value, datetime=commit_result.datetime)
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
# projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template']
# projects = ['git/dispatch']
# projects = ['git/fastapi']

projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template', 'git/dispatch', 'git/fastapi']

app = StateOf('Foo', commit_selection='year')
app.projects = projects
app.file_extensions = ['.py']


@app.metric(name='all_imports')
def all_imports(nodes: NodeList):
    import_nodes = ['import_statement', 'import_from_statement', 'future_import_statement']
    return nodes.count_types(import_nodes)


@app.metric(name='import_from_statement')
def import_from_statement(nodes: NodeList):
    return nodes.count_types(['import_from_statement'])


@app.metric(name='import_statement')
def import_statement(nodes: NodeList):
    return nodes.count_types(['import_statement'])


@app.metric(name='future_import_statement')
def future_import_statement(nodes: NodeList):
    return nodes.count_types(['future_import_statement'])


@app.metric('functions (LOC)')
def functions(nodes: NodeList):
    return nodes.loc_for_types(['function_definition'])


@app.metric(name='classes (LOC)')
def classes(nodes: NodeList):
    return nodes.loc_for_types(['class_definition'])

@app.metric(name='decorated')
def decorated(nodes: NodeList):
    return nodes.count_types(['decorated_definition'])

result = app.compute_metrics()

from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

for project_result in result.project_results:
    console = Console()
    table = Table(show_header=False)
    print(Panel(project_result.name, expand=False, style='red'))
    table.add_column("foo", style='green1')

    table.add_row('dates', *project_result.metric_values_with_missing_dates('functions', 'year')[0])

    for metric_name in result.metric_names:

        # print(project_result.commit_dates())
        # print(metric_name, project_result.metric_values(metric_name))
        # table.add_row(metric_name, *project_result.metric_values(metric_name))

        # print(project_result.metric_values_with_missing_dates('functions', 'year')[0])
        # print(project_result.metric_values_with_missing_dates('functions', 'year')[1])

        table.add_row(metric_name, *project_result.metric_values_with_missing_dates(metric_name, 'year')[1])

    console.print(table)
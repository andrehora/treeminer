import statistics

from datetime import datetime, date
from numbers import Number

from tree_sitter import Node
from treeminer.repo import Repo, Commit


def as_str(text: bytes) -> str:
    return text.decode('utf-8')

def pretty_dates(dates: list[date], date_unit) -> list[str]:
    if date_unit == 'year':
        return [each.strftime('%Y') for each in dates]
    if date_unit == 'month':
        return [each.strftime('%m/%Y') for each in dates]
    
def generate_years(start_date: date, end_date: date) -> list[date]:
    dates = list(range(start_date.year, end_date.year+1))
    return [date(year, 1, 1) for year in dates]

def generate_months(start_date: date, end_date: date) -> list[date]:
    start_month = start_date.month
    start_year = start_date.year
    end_month = end_date.month
    end_year = end_date.year

    if start_year == end_year:
        dates = [(month, start_year) for month in range(start_month, end_month + 1)]
        return to_date(dates)

    start_year_months = [(month, start_year) for month in range(start_month, 13)]
    middle_years_months = [(month, year) for year in range(start_year + 1, end_year) for month in range(1, 13)]
    end_year_months = [(month, end_year) for month in range(1, end_month + 1)]

    return to_date(start_year_months + middle_years_months + end_year_months)

def ge(date1: date, date2: date, date_unit: str):
    if date_unit == 'year':
        return date1.year >= date2.year
    if date_unit == 'month':
        return date1.year >= date2.year and date1.month >= date2.month

def to_date(self, dates: list[tuple[int,int]]) -> list[date]:
    return [date(year, month, 1) for month, year in dates]


class MetricInfo:
    
    def __init__(self, name, callback):
        self._name = name
        self.callback = callback

    @property
    def name(self):
        if self._name is None:
            return self.callback.__name__
        return self._name

class SystemNodes:
    
    def __init__(self, nodes: list[Node]):
        self.nodes = nodes

    @property
    def size(self):
        return len(self.nodes)
    
    def count_by_type(self, node_types: list[str]) -> int:
        return len(self.find_by_type(node_types))
    
    def find_by_type(self, node_types: list[str]) -> list[Node]:
        nodes = []
        for node in self.nodes:
            if node.type in node_types:
                nodes.append(node)
        return nodes
    
    def loc_by_type(self, node_types: list[str], stat: str = 'median') -> Number | list[Number]:
        nodes = self.find_by_type(node_types)
        locs = [len(as_str(node.text).split('\n')) for node in nodes]
        operation = getattr(statistics, stat)
        return operation(locs)

class MetricHistory:

    def __init__(self, name: str, dates: list[str], values: list[Number]):
        self.name = name
        self.dates = dates
        self.values = values
    
    @property
    def values_as_str(self) -> list[str]:
        return [str(each) for each in self.values]
    
    def __str__(self):
        return f'{self.name} {self.dates} {str(self.values)}'
    
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

    def commit_dates(self) -> list[datetime]:
        return [commit_result.datetime.strftime('%m/%Y') for commit_result in self.commit_results]

    def metric_history(self, metric_name: str) -> MetricHistory:
        dates = self.commit_dates()
        values = [str(metric_result.value) for metric_result in self._metric_results(metric_name)]
        return MetricHistory(metric_name, dates, values)

    def metric_history_fill_missing_dates(self, metric_name: str, date_unit: str = 'year') -> MetricHistory:
        
        values = []
        dates = self.dates_by_unit(date_unit)
        
        metric_results = sorted(self._metric_results(metric_name), key=lambda each: each.datetime, reverse=True)
        for date in dates:
            for metric_result in metric_results:
                if ge(date, metric_result.datetime, date_unit):
                    values.append(metric_result.value)
                    break
        
        dates = pretty_dates(dates, date_unit)
        return MetricHistory(metric_name, dates, values)
    
    def dates_by_unit(self, date_unit) -> list[str]:
        start_date = self.commit_results[0].datetime.date()
        end_date = date.today()
        # end_date = self.commit_results[-1].datetime

        all_dates = []
        if date_unit == 'year':
            all_dates = generate_years(start_date, end_date)
        if date_unit == 'month':
            all_dates = generate_months(start_date, end_date)
        
        return all_dates
        # return self._pretty_dates(all_dates, date_unit)
    
    def _metric_results(self, metric_name: str) -> list[MetricResult]:
        values = []
        for commit_result in self.commit_results:
            for metric_result in commit_result.metric_results:
                if metric_result.name == metric_name:
                    values.append(metric_result)
        return values

class Result:

    def __init__(self):
        self.project_results: list[ProjectResult] = []
        self.metric_names: list[str] = []

    def add_project_result(self, project_result: ProjectResult):
        self.project_results.append(project_result)

    def add_metric_name(self, name):
        self.metric_names.append(name)

    def merged_dates(self, date_unit: str = 'year'):
        merged_dates = set()
        for project_result in result.project_results:
            dates = project_result.dates_by_unit(date_unit)
            merged_dates.update(dates)
        return pretty_dates(sorted(list(merged_dates)), date_unit)

    def metric_history_fill_missing_dates(self, metric_name: str, date_unit: str = 'year'):

        dates = self.merged_dates()
        for project_result in result.project_results:
            metric_history = project_result.metric_history_fill_missing_dates(metric_name, date_unit)
            for each_date in dates:
                print(each_date)
                

class StateOf:

    def __init__(self, name: str, projects: list[str], file_extensions: list[str] | None, commit_selection: str | None = 'year'):

        self.name = name
        self.projects = projects
        self.file_extensions = file_extensions
        self.commit_selection = commit_selection

        self.registered_metrics: list[MetricInfo] = []
        self.analyzed_commits: list[str] = []

        only_releases = False
        if commit_selection == 'release':
            only_releases = True
        self._repo = Repo(self.projects, only_releases=only_releases)

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
                node_list = SystemNodes(commit_nodes)
                
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
# projects = ['git/dispatch']
# projects = ['git/fastapi']
projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template']
# projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template', 'git/dispatch', 'git/fastapi']

app = StateOf('Foo', projects=projects, file_extensions=['.py'], commit_selection='year')


# @app.metric(name='all_imports')
# def all_imports(nodes: NodeList):
#     import_nodes = ['import_statement', 'import_from_statement', 'future_import_statement']
#     return nodes.count_by_type(import_nodes)

# @app.metric(name='import_from_statement')
# def import_from_statement(nodes: NodeList):
#     return nodes.count_by_type(['import_from_statement'])

# @app.metric(name='import_statement')
# def import_statement(nodes: NodeList):
#     return nodes.count_by_type(['import_statement'])

# @app.metric(name='future_import_statement')
# def future_import_statement(nodes: NodeList):
#     return nodes.count_by_type(['future_import_statement'])

# @app.metric(name='classes (LOC)')
# def classes(nodes: NodeList):
#     return nodes.loc_by_type(['class_definition'])

# @app.metric(name='decorated')
# def decorated(nodes: NodeList):
#     return nodes.count_by_type(['decorated_definition'])

@app.metric('functions')
def functions(nodes: SystemNodes):
    return nodes.loc_by_type(['function_definition'], 'mean')

result = app.compute_metrics()
m = result.metric_history_fill_missing_dates('functions', 'year')
print(m)

# for project_result in result.project_results:
#     dates = project_result.metric_history_fill_missing_dates('functions', 'year').dates
#     print(dates)

#     for metric_name in result.metric_names:
#         values = project_result.metric_history_fill_missing_dates(metric_name, 'year').values_as_str
#         print(values)
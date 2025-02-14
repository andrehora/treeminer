import statistics
import json

from datetime import date, datetime
from numbers import Number
from collections import Counter

from tree_sitter import Node
from treeminer.repo import Repo, Commit

from rich.console import Console
from rich.table import Table


def as_str(text: bytes) -> str:
    return text.decode('utf-8')

def aggregate_basic(values: list[Number], measure: str) -> Number:
    if measure == 'max':
        return max(values)
    if measure == 'min':
        return min(values)
    return round(sum(values), 1)

def aggregate_stat(values: list[Number], measure: str) -> Number:
    operation = getattr(statistics, measure)
    result = operation(values)
    return round(result, 1)

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
                 categorical: bool, aggregate: str, group: str):
        
        self._name = name
        self.callback = callback
        self.file_extension = file_extension
        self.categorical = categorical
        self.aggregate = aggregate
        self._group = group

    @property
    def name(self) -> str:
        if self._name is None:
            return self.callback.__name__
        return self._name.strip()
    
    @property
    def name_or_none_for_categorical(self) -> str | None:
        if self.categorical:
            return None
        return self.name
    
    @property
    def group(self) -> str:
        if self._group is None:
            return self.name
        return self._group.strip()
    
class BeforeCommitInfo:

    def __init__(self, file_extension: str):
        self.file_extension = file_extension
    
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
    def values_as_str(self) -> list[str]:
        return [str(value) for value in self.values]
    
    @property
    def dates_and_values(self):
        return list(zip(self.dates, self.values))
    
    def __str__(self):
        return f'{self.name} {str(self.values)}'
    
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
        dates = self.date_steps()
        values = []
        
        metric_results = sorted(self._metric_results(metric_name), key=lambda m: m.date, reverse=True)
        for date_step in dates:
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
        
        assert len(dates) == len(values), f'{len(dates)} != {len(values)}'

        dates = DateUtil.formatted_dates(dates)
        return MetricEvolution(metric_name, dates, values)
    
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
        self.metrics_meta = MetricsMeta()

    @property
    def metric_names(self) -> list[str]:
        return self.metrics_meta.names
    
    @property
    def metric_dates(self) -> list[str]:
        return DateUtil.formatted_dates(self._date_steps())
    
    @property
    def metric_groups(self):
        return self.metrics_meta._groups_and_names
    
    def add_metric_aggregate(self, name: str, aggregate: str):
        self.metrics_meta.add_metric_aggregate(name, aggregate)

    def add_metric_group(self, name: str | None, group: str):
        self.metrics_meta.add_metric_group(name, group)

    def add_project_result(self, project_result: ProjectResult):
        self.project_results.append(project_result)
    
    def evolutions(self) -> list[MetricEvolution]:
        metric_evolutions = []
        for metric_name, metric_agg in self.metrics_meta.names_and_aggregates:
            metric_evo = self._metric_evolution(metric_name, metric_agg)
            metric_evolutions.append(metric_evo)
        return metric_evolutions
    
    def as_html(self):
        return HtmlReport(self).generate_html()

    def as_table(self):
        return TableReport(self).generate_table()
    
    def as_rich_table(self):
        table_data = TableReport(self).generate_table()
        RichTableReport(table_data).print()
    
    def _date_steps(self) -> list[date]:
        dates = set()
        for project_result in result.project_results:
            project_dates = project_result.date_steps()
            dates.update(project_dates)
        return sorted(list(dates))

    def _metric_evolution(self, metric_name: str, aggregate: str) -> MetricEvolution:
        # If one project, just return its dates and values
        if len(self.project_results) == 1:
            project = self.project_results[0]
            values = project.metric_evolution(metric_name).values
            return MetricEvolution(metric_name, self.metric_dates, values)

        # If multiples projects, we need to aggregate the values...
        values_by_date = {date: [] for date in self.metric_dates}

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

        return MetricEvolution(metric_name, self.metric_dates, values)

class MetricsMeta:

    def __init__(self):
        self._names_and_aggregates: dict[str, str] = {}
        self._groups_and_names: dict[str, set] = {}

    @property
    def names(self) -> list[str]:
        return list(self._names_and_aggregates.keys())
    
    @property
    def names_and_aggregates(self):
        return self._names_and_aggregates.items()

    def add_metric_aggregate(self, name: str, aggregate: str):
        if name in self._names_and_aggregates:
            return
        self._names_and_aggregates[name] = aggregate

    def add_metric_group(self, name: str | None, group: str):
        if name is None:
            self._groups_and_names[group] = set()
            return

        if group not in self._groups_and_names:
            self._groups_and_names[group] = {name}
        self._groups_and_names[group].add(name)
                
class GitEvo:

    def __init__(self, projects: list[str], file_extension: str | None = None, 
                 date_unit: str = 'year', since_year: int | None = None):
        
        if date_unit not in ['year', 'month']:
            raise BadDateUnit('date_unit must be year or month')

        self.projects = projects
        self.global_file_extension = file_extension
        self.date_unit = date_unit
        self.since_year = since_year

        self.registered_metrics: list[MetricInfo] = []
        self.registered_before_commits: list[BeforeCommitInfo] = []

        self._analyzed_commits: list[str] = []
        self._repo = Repo(self.projects)

    def metric(self, name: str = None,
               *,
               file_extension: str | None = None, 
               categorical: bool = False, 
               aggregate: str = 'sum',
               group: str | None = None):
        
        def decorator(func):
            self.registered_metrics.append(
                MetricInfo(name=name, 
                           callback=func,
                           file_extension=file_extension,
                           categorical=categorical,
                           aggregate=aggregate,
                           group=group))
            return func
        
        return decorator
    
    def before(self, file_extension: str | None = None):

        def decorator(func):
            self.registered_before_commits.append(
                BeforeCommitInfo(file_extension))    
            return func
        
        return decorator
    
    def compute(self) -> Result:
        
        # Sanity checks on registered_metrics
        result = Result(self.date_unit)
        for metric_info in self.registered_metrics:

            if self.global_file_extension is None and metric_info.file_extension is None:
                raise FileExtensionNotFound(f'file_extension should be defined globally or in metric {metric_info.name}')
            
            if metric_info.aggregate not in ['median', 'mean', 'mode', 'sum', 'max', 'min']:
                raise BadAggregate(f'aggregate in metric {metric_info.name} should be median, mean, mode, sum, max, or min')
            
            if metric_info.file_extension is None:
                metric_info.file_extension = self.global_file_extension
            
            # Real names of the categorical metrics are known only at runtime, thus, now register None
            result.add_metric_group(metric_info.name_or_none_for_categorical, metric_info.group)
                
        project_result = None
        project_name = ''
        project_commits = set()

        for commit in self._repo.commits:
            
            # Create new project result if new project name
            if project_name != commit.project_name:
                print(f'Analyzing {commit.project_name}')
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

            # Create and cache parsed commits for each file extension, eg, .py, .js, .java, etc
            parsed_commits = ParsedCommits(commit, self._all_file_extensions())

            # Iterate on each metric
            commit_result = CommitResult(commit.hash, commit.committer_date.date())
            for metric_info in self.registered_metrics:
                
                # Inject parsed_commit and run the metric callback
                parsed_commit = parsed_commits.get_parsed_commit_for(metric_info.file_extension)
                metric_value = metric_info.callback(parsed_commit)

                # Process categorical metrics
                if metric_info.categorical: 

                    if not isinstance(metric_value, list):
                        raise BadReturnType(f'categorical metric {metric_info.name} should return list of strings')

                    for real_name, value in Counter(metric_value).most_common():
                        assert isinstance(real_name, str), f'categorical metric {metric_info.name} should return list of strings'
                        metric_result = MetricResult(name=real_name, value=value, date=commit_result.date)
                        commit_result.add_metric_result(metric_result)
                        
                        # Register the real name of the categorical metric
                        result.add_metric_group(real_name, metric_info.group)
                        result.add_metric_aggregate(real_name, metric_info.aggregate)
                
                # Process numerical metrics
                else:
                    
                    if not isinstance(metric_value, (int, float)):
                        raise BadReturnType(f'numerical metric {metric_info.name} should return int or float')

                    metric_result = MetricResult(name=metric_info.name, value=metric_value, date=commit_result.date)
                    commit_result.add_metric_result(metric_result)

                    result.add_metric_aggregate(metric_info.name, metric_info.aggregate)

            print(f'- Date: {selected_date}, commit: {commit.hash}, processed files: {parsed_commits.file_stats()}')
            project_result.add_commit_result(commit_result)
        
        return result
        
    def _all_file_extensions(self):
        return set([metric_info.file_extension for metric_info in self.registered_metrics])
    
class ParsedCommits:

    def __init__(self, commit: Commit, file_extensions: list[str]):
        self.commit = commit
        self.file_extensions = file_extensions
        
        self._parsed_commits: dict[str, ParsedCommit] = {}
        self._create_parsed_commits()

    def get_parsed_commit_for(self, file_extension: str) -> ParsedCommit:
        assert file_extension in self.file_extensions
        return self._parsed_commits[file_extension]

    def file_stats(self):
        file_stats = [f'{extension} {len(pc.parsed_files)}' for extension, pc in self._parsed_commits.items()]
        return ' '.join(file_stats)
    
    def _create_parsed_commits(self):
        for file_extension in self.file_extensions:
            self._parsed_commits[file_extension] = self._create_parsed_commit(file_extension)

    def _create_parsed_commit(self, file_extension: str) -> ParsedCommit:
        parsed_files = []
        for file in self.commit.all_files([file_extension]):
            file_nodes = [node for node in file.tree_nodes]
            parsed_file = ParsedFile(file.filename, file.path, file_nodes)
            parsed_files.append(parsed_file)
        return ParsedCommit(self.commit.hash, self.commit.committer_date, parsed_files)
    
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

class RichTableReport:

    def __init__(self, table_data: list[list[str]]):
        self.table_data = table_data

    def print(self):
        table = Table()
        columns = self.table_data[0]
        for column in columns:
            style = 'bright_magenta'
            if column == 'date': style="green"
            table.add_column(column, justify="right", style=style, no_wrap=True)

        for row in self.table_data[1:]:
            table.add_row(*row)

        console = Console()
        console.print(table)

class TableReport:

    DATE_COLUMN_NAME = 'date'
    
    def __init__(self, result: Result):
        self.metric_names = result.metric_names
        self.metric_dates = result.metric_dates
        self.evolutions = result.evolutions()
    
    def generate_table(self) -> list[list[str]]:
        header = self._header()
        t_values = self.transpose_matrix(self._values())
        assert len(header) == len(t_values[0])
        t_values.insert(0, header)
        return t_values
    
    def generate_table2(self) -> list[list[str]]:
        return self.transpose_matrix(self.generate_table())

    def transpose_matrix(self, matrix: list[list]) -> list[list]:
        return [list(row) for row in zip(*matrix)]
    
    def _header(self) -> list[str]:
        return [self.DATE_COLUMN_NAME] + self.metric_names
    
    def _values(self) -> list[list[str]]:
        values = [evo.values_as_str for evo in self.evolutions]
        values.insert(0, self.metric_dates)
        return values
    
class Chart:

    colors = ["#36A2EB80", "#FF638480", "#FF9F4080", "#FFCE5680", "#4BC0C080", "#9966FF80", "#C9CBCF80"]

    def __init__(self, title: str, metric_names: list[str], metric_dates: list[str], evolutions: list[MetricEvolution]):
        assert len(metric_names) == len(evolutions)
        self.title = title
        self.metric_names = metric_names
        self.metric_dates = metric_dates
        self.evolutions = sorted(evolutions, key=lambda evo: evo.values[-1], reverse=True)
        
    def evo_dict(self) -> dict:
        return {
            'title': self.title,
            'type': 'line',
            'display_legend': self.has_multi_metrics,
            'labels': self.metric_dates,
            'datasets': self._evo_datasets()
        }
    
    def version_dict(self, chart_type: str = 'doughnut') -> dict:
        last_date = self.metric_dates[-1]
        return {
            'title': f'{self.title} in {last_date} (%)',
            'type': chart_type,
            'display_legend': False if chart_type == 'bar' else True,
            'labels': self._version_labels(),
            'datasets': self._version_dataset()
        }
    
    @property
    def has_single_metric(self):
        return len(self.evolutions) == 1
    
    @property
    def has_multi_metrics(self):
        return not self.has_single_metric
    
    def _version_labels(self) -> list[str]:
        return [evo.name for evo in self.evolutions]
    
    def _version_dataset(self) -> list[Number]:
        # Get the most recent metric values (this year) 
        total = sum([evo.values[-1] for evo in self.evolutions])
        ratios = [round(evo.values[-1]/total*100, 0) for evo in self.evolutions]
        return [{'data': ratios}]
    
    def _evo_datasets(self) -> list:
        if self.has_single_metric:
            return [{'data': self.evolutions[0].values}]
        
        return [{'label': evo.name, 
                 'data': evo.values} for evo in self.evolutions]
        

class HtmlReport:

    HTML_FILENAME = 'index.html'
    TEMPLATE_HTML_FILENAME = 'template.html'

    JSON_DATA_PLACEHOLDER = '{{JSON_DATA}}'
    TITLE_PLACEHOLDER = '{{TITLE}}'
    CREATED_DATE_PLACEHOLDER = '{{CREATED_DATE}}'

    def __init__(self, result: Result):
        self.metric_names = result.metric_names
        self.metric_dates = result.metric_dates
        self.metric_groups = result.metric_groups
        self.evolutions = result.evolutions()

    def generate_html(self):
        json_data = self._json_data()
        template = self._read_template()
        content = self._replace_json_data(template, json_data)
        content = self._replace_title(content, 'Python syntax and features')
        content = self._replace_created_date(content)
        self._write_html(content)

    def _json_data(self):
        return self._build_charts()

    def _build_charts(self) -> list[dict]:
        charts = []
        for group_name, metric_names in self.metric_groups.items():
            evolutions = self._find_metric_evolutions(metric_names)
            
            # Build evolution chart
            evo_chart = Chart(group_name, metric_names, self.metric_dates, evolutions)
            charts.append(evo_chart.evo_dict())

            # Build version chart if there are multiple metrics in evo chart
            if evo_chart.has_multi_metrics:
                charts.append(evo_chart.version_dict())

        return charts
            
    def _find_metric_evolutions(self, metric_names):
        return [evolution for evolution in self.evolutions if evolution.name in metric_names]
    
    def _read_template(self):
        with open(self.TEMPLATE_HTML_FILENAME, 'r') as template_file:
            template = template_file.read()
        return template

    def _write_html(self, html_content):
        with open(self.HTML_FILENAME, 'w') as output_file:
            output_file.write(html_content)

    def _replace_json_data(self, source, json_data):
        return source.replace(self.JSON_DATA_PLACEHOLDER, json.dumps(json_data, indent=3))

    def _replace_title(self, source, content):
        return source.replace(self.TITLE_PLACEHOLDER, content)

    def _replace_created_date(self, source):
        now = str(datetime.now().astimezone())
        return source.replace(self.CREATED_DATE_PLACEHOLDER, now)

# projects = ['git/cpython']
# projects = ['git/FastAPI-template']
projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template']
# projects = ['git/FastAPI-template', 'git/full-stack-fastapi-template', 'git/dispatch', 'git/fastapi']
# projects = projects + ['git/pytorch', 'git/ansible', 'git/core', 'git/django', 'git/rich', 'git/requests', 'git/cpython']


evo = GitEvo(projects=projects, file_extension='.py', date_unit='year', since_year=2020)

@evo.before(file_extension='.py')
def before(commit: ParsedCommit):
    print('before')
    return commit

@evo.metric('Analyzed files', aggregate='sum', file_extension='.js')
def files(commit: ParsedCommit):
    return len(commit.parsed_files)

@evo.metric('Most used data structures', aggregate='sum', categorical=True)
def data_structure(commit: ParsedCommit):
    return commit.node_types(['dictionary', 'list', 'set', 'tuple'])

@evo.metric('Most used comprehensions', aggregate='sum', categorical=True)
def comprehension(commit: ParsedCommit):
    return commit.node_types(['dictionary_comprehension', 'list_comprehension', 'set_comprehension'])

@evo.metric('Most used control flows', aggregate='sum', categorical=True)
def control_flow(commit: ParsedCommit):
    return commit.node_types(['for_statement', 'while_statement', 'if_statement', 'try_statement', 'match_statement', 'with_statement'])

@evo.metric('for vs. while', aggregate='sum', categorical=True)
def for_while(commit: ParsedCommit):
    return commit.node_types(['for_statement', 'while_statement'])

@evo.metric('continue vs. break', aggregate='sum', categorical=True)
def continue_break(commit: ParsedCommit):
    return commit.node_types(['break_statement', 'continue_statement'])

@evo.metric('integer vs. float', aggregate='sum', categorical=True)
def int_float(commit: ParsedCommit):
    return commit.node_types(['integer', 'float'])

@evo.metric('Function LOC (median)', aggregate='median')
def functions(commit: ParsedCommit):
    return commit.loc('function_definition', 'median')

@evo.metric('return vs. yield', aggregate='sum', categorical=True)
def return_yield(commit: ParsedCommit):
    return commit.node_types(['return_statement', 'yield'])

@evo.metric('Exceptions', aggregate='sum', categorical=True)
def exceptions(commit: ParsedCommit):
    return commit.node_types(['try_statement', 'raise_statement'])

@evo.metric('Most used import types', categorical=True)
def imports(commit: ParsedCommit):
    return commit.node_types(['import_statement', 'import_from_statement', 'future_import_statement'])

@evo.metric('Typed and default parameters', aggregate='sum', categorical=True)
def parameter_type(commit: ParsedCommit):
    return commit.node_types(['default_parameter', 'typed_parameter', 'typed_default_parameter'])

@evo.metric('Parameter dictionary vs. list splat pattern', aggregate='sum', categorical=True)
def parameter_splat_pattern(commit: ParsedCommit):
    return commit.node_types(['dictionary_splat_pattern', 'list_splat_pattern'])

@evo.metric('Decorated definitions', aggregate='sum')
def asserts(commit: ParsedCommit):
    return commit.count_nodes(['decorated_definition'])

@evo.metric('assert', aggregate='sum')
def asserts(commit: ParsedCommit):
    return commit.count_nodes(['assert_statement'])

@evo.metric('lambda', aggregate='sum')
def lambdas(commit: ParsedCommit):
    return commit.count_nodes(['lambda'])

@evo.metric('await', aggregate='sum')
def awaits(commit: ParsedCommit):
    return commit.count_nodes(['await'])

@evo.metric('pass', aggregate='sum')
def passes(commit: ParsedCommit):
    return commit.count_nodes(['pass_statement'])


# @evo.metric('Number of nodes', aggregate='sum')
# def unnamed_nodes(commit: ParsedCommit):
#     return commit.count_nodes()

# @evo.metric('All files', aggregate='sum', group='Files')
# def python_files(commit: ParsedCommit):
#     return len(commit.parsed_files)

# @evo.metric('Test files', aggregate='sum', group='Files')
# def test_files(commit: ParsedCommit):
#     return len([file.name for file in commit.parsed_files if 'test' in file.path])

# @evo.metric('Number of imports')
# def all_imports(commit: ParsedCommit):
#     import_nodes = ['import_statement', 'import_from_statement', 'future_import_statement']
#     return commit.count_nodes(import_nodes)

# @evo.metric('Imports', categorical=True, group='Types of Import')
# def imports(commit: ParsedCommit):
#     return commit.node_types(['import_statement', 'import_from_statement', 'future_import_statement'])

# @evo.metric('Number of classes', aggregate='sum', group='Entities')
# def decorated(commit: ParsedCommit):
#     return commit.count_nodes(['class_definition'])

# @evo.metric('Number of functions', aggregate='sum', group='Entities')
# def decorated(commit: ParsedCommit):
#     return commit.count_nodes(['function_definition'])

# @evo.metric('Classes', aggregate='median', group='LOC')
# def classes(commit: ParsedCommit):
#     return commit.loc('class_definition', 'median')

# @evo.metric('Functions', aggregate='median', group='LOC')
# def functions(commit: ParsedCommit):
#     return commit.loc('function_definition', 'median')

result = evo.compute()
table = result.as_html()

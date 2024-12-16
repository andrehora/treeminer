import logging
from datetime import datetime
from pathlib import Path
from typing import Generator

from git import Repo as GitRepository, Blob

import lizard
from pydriller import Repository as PydrillerRepository, Git as PydrillerGit
from pydriller.domain.commit import Commit as PydrillerCommit, ModifiedFile as PydrillerModifiedFile

from github import Github as GithubAPI
from github import Auth

from tree_sitter import Language, Parser, Tree, Node
import tree_sitter_python, tree_sitter_java, tree_sitter_javascript
from lang_types import python, java, javascript

logger = logging.getLogger(__name__)

def traverse_tree(tree: Tree) -> Generator[Node, None, None]:
    cursor = tree.walk()

    visited_children = False
    while True:
        if not visited_children:
            yield cursor.node
            # nodes.append(cursor.node)
            if not cursor.goto_first_child():
                visited_children = True
        elif cursor.goto_next_sibling():
            visited_children = False
        elif not cursor.goto_parent():
            break


class RepoGithubAPI:

    def __init__(self, repo_full_name: str, token_auth: Auth.Token = None):
        api = GithubAPI(auth=token_auth)
        self.repo = api.get_repo(repo_full_name)

    @property
    def topics(self):
        return self.repo.get_topics()

    @property
    def stars(self):
        return self.repo.stargazers_count
    
    @property
    def forks(self):
        return self.repo.forks_count
    
    @property
    def watchers(self):
        return self.repo.watchers_count
    
    def issues(self, **kw):
        return self.repo.get_issues(**kw)
    
class File:

    def __init__(self, git_blob: Blob):
        self._git_blob = git_blob
        
        self._detect_language()
        lang = Language(self._lang_grammar.language())
        parser = Parser(lang)
        self._tree = parser.parse(bytes(self.source_code, "utf-8"))

    @property
    def classes(self) -> list[Node]:
        return self._find_nodes_by_constructor('classes')

    @property
    def methods(self) -> list[Node]:
        return self._find_nodes_by_constructor('methods')
    
    @property
    def calls(self) -> list[Node]:
        return self._find_nodes_by_constructor('calls')
    
    @property
    def comments(self) -> list[Node]:
        return self._find_nodes_by_constructor('comments')

    @property
    def tree(self):
        return traverse_tree(self._tree)
    
    @property
    def extension(self) -> str:
        return Path(self.path).suffix

    @property
    def filename(self) -> str:
        return Path(self.path).name

    @property
    def path(self) -> str:
        return self._git_blob.path

    @property
    def source_code(self) -> str:
        try:
            data = self._git_blob.data_stream.read()
            return data.decode("utf-8", "ignore")
        except:
            return None
    
    @property
    def lizard(self) -> list:
        analysis = lizard.analyze_file.analyze_source_code(self.filename, self.source_code)
        return analysis
    
    def _find_nodes_by_constructor(self, element):
        return self._find_nodes_by_types(self._lang_nodes[element])

    def _find_nodes_by_types(self, node_types) -> list[Node]:
        nodes = []
        for node in self.tree:
            if node.type in node_types:
                nodes.append(node)
        return nodes
    
    def _detect_language(self):
        if self.extension == '.py':
            self._lang_grammar = tree_sitter_python
            self._lang_nodes = python
        if self.extension == '.java':
            self._lang_grammar = tree_sitter_java
            self._lang_nodes = java
        if self.extension == '.js':
            self._lang_grammar = tree_sitter_javascript
            self._lang_nodes = javascript


class ModifiedFile(File):
    pass
    
class Commit:

    def __init__(self, pydriller_commit: PydrillerCommit):
        self._pydriller_commit = pydriller_commit
        self._git_commit = self._pydriller_commit._c_object

    @property
    def hash(self) -> str:
        return self._pydriller_commit.hash
    
    def modified_files(self, formats: list[str] = None) -> list[ModifiedFile]:
        return self._pydriller_commit.modified_files

    def files(self, extensions: list[str] = None) -> list[File]:
        _files = []
        for item in self._git_commit.tree.traverse():
            if item.type == "blob":
                if extensions is not None:
                    for extension in extensions:
                        if item.path.endswith(f'.{extension}'):
                            _files.append(File(item))
                else:
                    _files.append(File(item))
        return _files


class Repo(PydrillerRepository):

    def __init__(self, path_to_repo: str, 
                token_auth: str = None,
                single: str = None,
                since: datetime = None, to: datetime = None, 
                from_commit: str = None, to_commit: str = None, 
                from_tag: str = None, to_tag: str = None,
                only_releases: bool = False):
                
        super().__init__(path_to_repo=path_to_repo, single=single, since=since, to=to, 
                         from_commit=from_commit, to_commit=to_commit, from_tag=from_tag, to_tag=to_tag, only_releases=only_releases)
        
        self.path_to_repo = path_to_repo
        self.repo_url = self._ensure_repo_url(path_to_repo)

        # auth = None
        # if token_auth is not None:
        #     auth = Auth.Token(token_auth)
        # self.api = RepoGithubAPI(self.repo_full_name, auth)

    def _iter_commits(self, pydriller_commit: PydrillerCommit) -> Generator[Commit, None, None]:
        logger.info(f'Commit #{pydriller_commit.hash} in {pydriller_commit.committer_date} from {pydriller_commit.author.name}')

        if self._conf.is_commit_filtered(pydriller_commit):
            logger.info(f'Commit #{pydriller_commit.hash} filtered')
            return

        yield Commit(pydriller_commit)

    @property
    def lastest_commit(self) -> Commit:
        git = PydrillerGit(self.path_to_repo)
        pydriller_commit = git.get_head()
        git.clear()
        return Commit(pydriller_commit)
    
    @property
    def repo_org(self):
        return self.repo_url.split('/')[-2]
    
    @property
    def repo_name(self):
        return self.repo_url.split('/')[-1]
    
    @property
    def repo_full_name(self):
        return f'{self.repo_org}/{self.repo_name}'
    
    def _ensure_repo_url(self, path_to_repo):
        if self._is_remote(path_to_repo):
            return path_to_repo
        repo = GitRepository(path_to_repo)
        url = repo.remotes.origin.url
        repo.git.clear_cache()
        return url

    def _is_remote(self, repo):
        return repo.startswith(("git@", "https://", "http://", "git://"))


repo = Repo('pydriller')
# print(repo.api.stars)

files = repo.lastest_commit.files(['py'])
file = files[3]

print(len(file.classes))
print(len(file.methods))
print(len(file.calls))
print(len(file.comments))


# commits = repo.traverse_commits()
# for commit in commits:
#     print(len(commit.files(['py'])))

import logging
from pathlib import Path
from typing import Generator

import lizard

from git import Repo as GitRepository, Blob

from pydriller import Repository as PydrillerRepository, Git as PydrillerGit
from pydriller.domain.commit import Commit as PydrillerCommit, ModifiedFile as PydrillerModifiedFile

from github import Github as GithubAPI
from github import Auth
from datetime import datetime

logger = logging.getLogger(__name__)


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

    def files(self, formats: list[str] = None) -> list[File]:
        _files = []
        for item in self._git_commit.tree.traverse():
            if item.type == "blob":
                if formats is not None:
                    for format in formats:
                        if item.path.endswith(f'.{format}'):
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

        auth = None
        if token_auth is not None:
            auth = Auth.Token(token_auth)
        self.api = RepoGithubAPI(self.repo_full_name, auth)

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

l = file.lizard
print(file.path)
for f in l.function_list:
    print(f)

# commits = repo.traverse_commits()
# for commit in commits:
#     print(len(commit.files(['py'])))

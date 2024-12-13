from git import Repo as GitRepository
from pydriller import Repository as PydrillerRepository
from github import Github as GithubAPI
from github import Auth
from datetime import datetime


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


class Repo(PydrillerRepository):

    def __init__(self, path_to_repo: str, 
                 token_auth: str = None,
                 since: datetime = None, to: datetime = None, 
                 from_commit: str = None, to_commit: str = None, 
                 from_tag: str = None, to_tag: str = None):

        self.path_to_repo = path_to_repo
        self.git = GitRepository(self.path_to_repo)
        self._pydriller_repo = PydrillerRepository(path_to_repo=path_to_repo, since=since, to=to, from_commit=from_commit, 
                                                   to_commit=to_commit, from_tag=from_tag, to_tag=to_tag) 
        auth = None
        if token_auth is not None:
            auth = Auth.Token(token_auth)
        self.api = RepoGithubAPI(self.repo_full_name, auth)

    @property
    def repo_url(self):
        if self._is_remote(self.path_to_repo):
            return self.path_to_repo
        return self.git.remotes.origin.url
    
    @property
    def repo_org(self):
        return self.repo_url.split('/')[-2]
    
    @property
    def repo_name(self):
        return self.repo_url.split('/')[-1]
    
    @property
    def repo_full_name(self):
        return f'{self.repo_org}/{self.repo_name}'

    @staticmethod
    def _is_remote(repo):
        return repo.startswith(("git@", "https://", "http://", "git://"))


repo = Repo('pydriller')

print(repo.repo_full_name)
print(repo.repo_url)
print(repo.api.stars)
print(repo.api.topics)

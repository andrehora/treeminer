from git import Repo as GitRepository
from pydriller import Repository as PydrillerRepository
from github import Github as GithubAPI
from github import Auth


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

    _api: RepoGithubAPI = None
    _git: GitRepository = None

    def set_token_auth(self, token_auth: str):
        auth = Auth.Token(token_auth)
        self._api = RepoGithubAPI(self.repo_full_name, auth)

    @property
    def api(self) -> RepoGithubAPI:
        if self._api is None:
            self._api = RepoGithubAPI(self.repo_full_name)
        return self._api
    
    @property
    def git(self):
        if self._git is None:
            self._git = GitRepository(self._path_to_repo)
        return self._git

    @property
    def repo_url(self):
        if self._is_remote(self._path_to_repo):
            return self._path_to_repo
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
    
    @property
    def _path_to_repo(self):
        return self._conf.get('path_to_repo')

    @staticmethod
    def _is_remote(repo):
        return repo.startswith(("git@", "https://", "http://", "git://"))


repo = Repo('pydriller')

print(repo.repo_full_name)
print(repo.repo_url)
print(repo.api.stars)
print(repo.api.topics)


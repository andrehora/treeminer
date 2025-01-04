import logging
from datetime import datetime
from pathlib import Path
from typing import Generator
from abc import abstractmethod

from git import Blob as GitBlob

from pydriller import Repository as PydrillerRepository, Git as PydrillerGit
from pydriller.domain.commit import Commit as PydrillerCommit, ModifiedFile as PydrillerModifiedFile

from tree_sitter import Language, Parser, Node, Tree
from miners import BaseMiner, buildin_miners

logger = logging.getLogger(__name__)

    
class CodeParser:

    def __init__(self, source_code: str, tree_sitter_grammar):
        lang_grammar = Language(tree_sitter_grammar.language())
        parser = Parser(lang_grammar)
        self._tree = parser.parse(bytes(source_code, "utf-8"))

    @property
    def tree(self) -> Tree:
        return self._tree
    
    @property
    def nodes(self) -> list[Node]:
        return self._traverse_tree()

    def _traverse_tree(self) -> Generator[Node, None, None]:
        cursor = self._tree.walk()
        visited_children = False
        while True:
            if not visited_children:
                yield cursor.node
                if not cursor.goto_first_child():
                    visited_children = True
            elif cursor.goto_next_sibling():
                visited_children = False
            elif not cursor.goto_parent():
                break

class BaseFile:

    @property
    @abstractmethod
    def filename(self) -> str:
        pass

    @property
    @abstractmethod
    def extension(self) -> str:
        pass

    @property
    @abstractmethod
    def source_code(self) -> str:
        pass

    @property
    def mine(self) -> BaseMiner:
        if self._miner is None:
            return BaseMiner()
        return self._miner(self._code_parser.nodes)


class File(BaseFile):

    def __init__(self, git_blob: GitBlob, miner: BaseMiner | None = None):
        self._git_blob = git_blob
        self._miner = miner
        if self._miner:
            self._code_parser = CodeParser(self.source_code, self._miner.tree_sitter_grammar)

    @property
    def filename(self) -> str:
        return Path(self.path).name
    
    @property
    def extension(self) -> str:
        return Path(self.path).suffix

    @property
    def source_code(self) -> str:
        try:
            data = self._git_blob.data_stream.read()
            return data.decode("utf-8", "ignore")
        except:
            return ''
        
    @property
    def path(self) -> str:
        return self._git_blob.path


class ModifiedFile(BaseFile):
    
    def __init__(self, pd_modified_file: PydrillerModifiedFile, miner: BaseMiner | None = None):
        self._pd_modified_file = pd_modified_file
        self._miner = miner
        if self._miner:
            self._code_parser = CodeParser(self.source_code, self._miner.tree_sitter_grammar)
    
    @property
    def filename(self) -> str:
        return self._pd_modified_file.filename
    
    @property
    def extension(self) -> str:
        return Path(self.filename).suffix
    
    @property
    def source_code(self) -> str:
        return self._pd_modified_file.source_code
    
    @property
    def source_code_before(self) -> str:
        return self._pd_modified_file.source_code_before
    
    @property
    def new_path(self) -> str:
        return self._pd_modified_file.new_path
    
    @property
    def old_path(self) -> str:
        return self._pd_modified_file.old_path
    
    @property
    def change_type(self) -> str:
        return self._pd_modified_file.change_type
    
    @property
    def info(self) -> PydrillerModifiedFile:
        return self._pd_modified_file
    
class Commit:

    def __init__(self, pd_commit: PydrillerCommit, miners: list[BaseMiner]):
        self._pd_commit = pd_commit
        self._git_commit = self._pd_commit._c_object
        self._miners = miners

    @property
    def hash(self) -> str:
        return self._pd_commit.hash
    
    @property
    def msg(self) -> str:
        return self._pd_commit.msg

    @property
    def info(self) -> PydrillerCommit:
        return self._pd_commit
    
    def modified_files(self, extensions: list[str] = None) -> list[ModifiedFile]:
        _modified_files = []
        for modified_file in self._pd_commit.modified_files:
            filename = modified_file.filename
            if extensions is not None:
                for extension in extensions:
                    if filename.endswith(extension):
                        miner = self._detect_file_miner(filename)
                        _modified_files.append(ModifiedFile(modified_file, miner))
            else:
                miner = self._detect_file_miner(filename)
                _modified_files.append(ModifiedFile(modified_file, miner))
        return _modified_files

    def all_files(self, extensions: list[str] = None) -> list[File]:
        _files = []
        for item in self._git_commit.tree.traverse():
            if item.type == "blob":
                filename = item.path
                if extensions is not None:
                    for extension in extensions:
                        if filename.endswith(extension):
                            miner = self._detect_file_miner(filename)
                            _files.append(File(item, miner))
                else:
                    miner = self._detect_file_miner(filename)
                    _files.append(File(item, miner))
        return _files
    
    def _detect_file_miner(self, filename):
        for miner in self._miners:
            if filename.endswith(miner.extension):
                return miner
        return None


class Repo(PydrillerRepository):

    def __init__(self, path_to_repo: str, 
                single: str = None,
                since: datetime = None, to: datetime = None, 
                from_commit: str = None, to_commit: str = None, 
                from_tag: str = None, to_tag: str = None,
                only_releases: bool = False):
                
        super().__init__(path_to_repo=path_to_repo, single=single, since=since, to=to, 
                         from_commit=from_commit, to_commit=to_commit, from_tag=from_tag, to_tag=to_tag, only_releases=only_releases)
    
        self.path_to_repo = path_to_repo
        self._miners = []
        self._miners.extend(buildin_miners)

    def add_miner(self, miner):
        self._miners.insert(0, miner) 

    @property
    def lastest_commit(self) -> Commit:
        git = PydrillerGit(self.path_to_repo)
        pd_commit = git.get_head()
        git.clear()
        return Commit(pd_commit, self._miners)

    def _iter_commits(self, pydriller_commit: PydrillerCommit) -> Generator[Commit, None, None]:
        logger.info(f'Commit #{pydriller_commit.hash} in {pydriller_commit.committer_date} from {pydriller_commit.author.name}')

        if self._conf.is_commit_filtered(pydriller_commit):
            logger.info(f'Commit #{pydriller_commit.hash} filtered')
            return

        yield Commit(pydriller_commit)

from miners import PythonMiner

class FastAPIMiner(PythonMiner):
    name = 'FastAPI'

    @property
    def decorators(self):
        return self.find_nodes_by_types(['decorator'])
    
    @property
    def endpoins(self):
        for decorator in self.decorators:
            print(decorator.text)
            node = decorator.children
            print(node)

repo = Repo('full-stack-fastapi-template')
# repo.add_miner(FastAPIMiner)
files = repo.lastest_commit.all_files()
for file in files:
    print(file.filename)
    print(len(file.mine.imports))
    print(len(file.mine.classes))
    print(len(file.mine.methods))
    # print(len(file.mine.calls))
    # print(len(file.mine.comments))
    # print(len(file.mine.decorators))
    # print(file.mine.endpoins)


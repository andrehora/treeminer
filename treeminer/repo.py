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
    def tree_nodes(self) -> list[Node]:
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
            

class Parsable:

    def __init__(self, miner: BaseMiner | None):
        self._miner = miner
        self._code_parser = None
        if self._miner:
            self._code_parser = CodeParser(self.source_code, self._miner.tree_sitter_grammar)

    @property
    def mine(self) -> BaseMiner:
        if self._miner is None:
            return BaseMiner()
        return self._miner(self._code_parser.tree_nodes)
    
    @property
    def tree_nodes(self) -> BaseMiner:
        if self._code_parser is None:
            return []
        return self._code_parser.tree_nodes

    @property
    @abstractmethod
    def source_code(self) -> str:
        pass


class File(Parsable):

    def __init__(self, git_blob: GitBlob, miner: BaseMiner | None):
        self._git_blob = git_blob
        super().__init__(miner)

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


class ModifiedFile(Parsable):
    
    def __init__(self, pd_modified_file: PydrillerModifiedFile, miner: BaseMiner | None):
        self._pd_modified_file = pd_modified_file
        super().__init__(miner)

    @property
    def filename(self) -> str:
        return self._pd_modified_file.filename
    
    @property
    def extension(self) -> str:
        return Path(self.filename).suffix
    
    @property
    def source_code(self) -> str:
        return self._pd_modified_file.source_code or ''
    
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
    
    @property
    def added_lines(self) -> list['ModifiedLine']:
        _added_lines = []
        for added_line in self._pd_modified_file.diff_parsed['added']:
            source_code = added_line[1]
            _added_lines.append(ModifiedLine(source_code, self._miner, is_added=True))
        return _added_lines
    
    @property
    def deleted_lines(self) -> list[str]:
        _deleted_lines = []
        for deleted_line in self._pd_modified_file.diff_parsed['deleted']:
            source_code = deleted_line[1]
            _deleted_lines.append(ModifiedLine(source_code, self._miner, is_deleted=True))
        return _deleted_lines


class ModifiedLine(Parsable):
    
    def __init__(self, source_code: str, miner: BaseMiner | None, is_added: bool = False, is_deleted: bool = False):
        self._source_code = source_code
        self._is_added = is_added
        self._is_deleted = is_deleted
        super().__init__(miner)

    @property
    def is_added(self) -> bool:
        return self._is_added
    
    @property
    def is_deleted(self) -> bool:
        return self._is_deleted
    
    @property
    def source_code(self) -> bool:
        return self._source_code


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
        pd_git = PydrillerGit(self.path_to_repo)
        pd_commit = pd_git.get_head()
        pd_git.clear()
        return Commit(pd_commit, self._miners)
    
    @property
    def commits(self) -> Generator[Commit, None, None]:
        return self.traverse_commits()

    def _iter_commits(self, pd_commit: PydrillerCommit) -> Generator[Commit, None, None]:
        logger.info(f'Commit #{pd_commit.hash} in {pd_commit.committer_date} from {pd_commit.author.name}')

        if self._conf.is_commit_filtered(pd_commit):
            logger.info(f'Commit #{pd_commit.hash} filtered')
            return

        yield Commit(pd_commit, self._miners)

from miners import PythonMiner

class FastAPIMiner(PythonMiner):
    name = 'FastAPI'

    @property
    def decorators(self):
        return self.find_nodes_by_types(['decorator'])


repo = Repo('full-stack-fastapi-template')
repo.add_miner(FastAPIMiner)

for commit in repo.commits:
    for file in commit.modified_files(['py']):
        for line in file.added_lines:
            for node in line.mine.extras:
                print(str(node.text))
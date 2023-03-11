"""本地上传."""
import hashlib
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid1

from werkzeug.datastructures import FileStorage, ImmutableMultiDict

from src.config import config
from src.util.exception import RequestParamsError


class Uploader:
    """本地上传.

    files: request.files
    """

    all_max_size: int = 1024 * 1024 * 10  # 所有图片不超过10M
    nums: int = 5  # 运行同时上传5张
    single_max_size: int = 1024 * 1024 * 2  # 单张大小不超过2M
    extensions: Iterable[str] = ("jpg", "jpeg", "png", "gif", "webp")
    path: Path | str | None = None  # 存储路径

    def __init__(self, files: ImmutableMultiDict[str, FileStorage]) -> None:
        """files: request.files."""
        self.init_config()
        self.file_storages: list[FileStorage] = []
        self.get_file_storage(files)
        self.verify()

    def init_config(self) -> None:
        # """优先使用 config 中配置项"""
        if self.path is None:
            self.path = Path(config.BASE_DIR) / "assets"
        else:
            self.path = Path(self.path)
        if not self.path.exists():
            Path(self.path).mkdir(parents=True, exist_ok=True)

    def get_file_storage(self, files: ImmutableMultiDict[str, FileStorage]) -> None:
        """files: request.files."""
        for key, _ in files.items():
            self.file_storages += files.getlist(key)

    def verify(self) -> None:
        """验证是否符合条件."""
        if self.file_storages == []:
            raise RequestParamsError(message="未传入文件")
        self._check_extention()
        self._check_size()

    def _check_extention(self) -> None:
        for _file in self.file_storages:
            filename = _file.filename or ""
            if "." not in filename:
                raise RequestParamsError(message="文件格式不正确")
            ext = filename.split(".")[-1]
            if ext not in self.extensions:
                raise RequestParamsError(message="文件格式不正确")

    def _check_size(self) -> None:
        lens = len(self.file_storages)
        if lens > self.nums:
            raise RequestParamsError(message="文件太多")

        total_size = 0
        for _file in self.file_storages:
            size = self.__get_size(_file)
            if size > self.single_max_size:
                raise RequestParamsError(message="文件太大")
            total_size += size
        if total_size > self.all_max_size:
            raise RequestParamsError(message="文件总体积过大")

    @staticmethod
    def __get_size(file: FileStorage) -> int:
        file.seek(0, 2)  # seek()跳到指定位置 2表示从文件末尾 0表示偏移量
        size: int = file.tell()  # tell() 获得当前指针位置 获得文件大小
        file.seek(0)  # 跳到文件起始位置
        return size

    @staticmethod
    def __get_ext(file: FileStorage) -> str:
        filename = file.filename or ""
        return filename.split(".")[-1]

    def rename(self, file: FileStorage) -> str:
        uuid = uuid1().hex
        return f"{uuid}.{self.__get_ext(file)}"

    @staticmethod
    def generate_md5(file: FileStorage) -> str:
        md5 = hashlib.md5()  # noqa
        md5.update(file.read())
        file.seek(0)
        return md5.hexdigest()

    def upload(self) -> list[dict[str, str]]:
        """存储在本地.

        TODO 增加数据库信息
        """
        result = []
        time = datetime.now(UTC)
        relation_path = f"{time.year}/{time.month}/{time.day}"
        path = Path(self.path or "") / relation_path
        path.mkdir(parents=True, exist_ok=True)
        for _file in self.file_storages:
            name = self.rename(_file)
            _file.save(str(path / name))
            result.append({"name": name, "path": relation_path})
        return result

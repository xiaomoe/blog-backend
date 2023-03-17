import re
from typing import Iterable, Type

from elasticsearch import Elasticsearch, NotFoundError
from flask import Flask, current_app
from sqlalchemy import event
from sqlmodel import Session, SQLModel, case, col, select

from src.common.db import session


class Searchable:
    model: Type[SQLModel]
    index_name: str
    __searchable__: Iterable[tuple[str, bool]] = set()

    zh_field_properties: dict[str, str] = {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_max_word",
    }  # 中文分词

    def __init__(self) -> None:
        if "es" not in current_app.extensions:
            raise Exception("请先在 app 中实例化 es 插件")
        self.es: Elasticsearch = current_app.extensions["es"]
        if self.index_name is None:
            self.index_name = str(self.model.__tablename__)
        if not hasattr(self.model, "id"):
            raise Exception("model 必须有 id 字段")
        self.listen()

    def create_index(self):
        """获得当前模型索引"""
        properties = {}
        for field, _ in self.__searchable__:
            properties[field] = self.zh_field_properties
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(index=self.index_name, mappings={"properties": properties})

    def add_obj_index(self, obj: SQLModel):
        """添加模型索引"""
        self.create_index()
        document = {}
        for field, _ in self.__searchable__:
            document[field] = getattr(obj, field)
        self.es.index(index=self.index_name, document=document)

    def remove_obj_index(self, obj: SQLModel):
        """删除模型索引"""
        try:
            self.es.delete(index=self.index_name, id=obj.id)  # type: ignore
        except NotFoundError:
            pass

    def highlight(self, q: str):
        """高亮"""
        tokens = self.es.indices.analyze(index=self.index_name, analyzer="ik_max_word", text=q)
        for token in tokens["tokens"]:
            q = re.sub(
                r"(%s)" % re.escape(token["token"]),
                "<span style='color: red; background: yellow;'>\g<1></span>",  # TODO 高亮模板
                q,
                flags=re.IGNORECASE,
            )
        return q

    def query_obj_index(self, q: str, page: int, count: int, ids: Iterable | None = None):
        """按条件查询
        q: 要查询的字段
        page: 默认1
        count: 默认10
        ids: 指定查询范围
        """
        query = {}
        if ids is None:
            query = {
                "multi_match": {
                    "query": q,
                    "fields": ["*"],
                }
            }
        else:
            # 查询指定文档
            query = {
                "bool": {
                    "must": {
                        "multi_match": {
                            "query": q,
                            "fields": ["*"],
                        }
                    },
                    "filter": {
                        "ids": {
                            "values": ids,
                        }
                    },
                }
            }
        result = self.es.search(
            query=query,
            from_=(page - 1) * count,
            size=count,
        )
        total = result["hits"]["total"]["value"]
        result_ids = [int(hit["_id"]) for hit in result["hits"]["hits"]]
        # items = [(int(hit["_id"]), hit["_score"]) for hit in result["hits"]["hits"]]
        return total, result_ids  # (total, [id])

    def search(self, q: str, page: int, count: int, ids: Iterable | None = None):
        """query_boj_index 的抽象"""
        total, result_ids = self.query_obj_index(q, page, count, ids)
        if total == 0:
            # 没有记录
            with session:
                return 0, session.exec(select(self.model).filter_by(id=0))
        # hit_ids = []  # 匹配到的记录，id 列表
        when = []
        for i in range(len(result_ids)):
            when.append((result_ids[i], i))
        # https://stackoverflow.com/questions/6332043/sql-order-by-multiple-values-in-specific-order/6332081#6332081
        with session:
            result = session.exec(
                select(self.model)
                .filter(col(self.model.id).in_(result_ids))  # type: ignore
                .order_by(case(when, value=self.model.id))  # type: ignore
            )
            # 再遍历 BaseQuery，将要搜索的字段值中关键词高亮
            for obj in result:
                for field, need_highlight in self.__searchable__:
                    if need_highlight:  # 只有设置为 True 的字段才高亮关键字
                        source = getattr(obj, field)  # 原字段的值
                        highlight_source = self.highlight(source)  # 关键字高亮后的字段值
                        setattr(obj, field, highlight_source)

            return total, result

    def reindex(self):
        """reindex 所有模型数据"""
        with session:
            result = session.exec(select(self.model)).all()
            for item in result:
                self.add_obj_index(item)

    def listen(self):
        """sqlalchemy 监听事件注册"""

        def after_insert(mapper, connection, target):
            """插入数据后需要添加到索引"""
            self.add_obj_index(target)

        def after_delete(mapper, connection, target):
            """删除数据后需要删除对应索引"""
            self.remove_obj_index(target)

        def before_commit(session: Session):
            session._changes = {"update": list(session.dirty)}  # type:ignore

        def after_commit(session):
            for obj in session._changes["update"]:
                if isinstance(obj, self.model):
                    self.add_obj_index(obj)
            session._changes = None

        event.listen(self.model, "after_insert", after_insert)
        event.listen(self.model, "after_delete", after_delete)
        # update 不一定保证是执行了 UPDATE 语句，所以使用 commit 判断？
        event.listen(session, "before_commit", before_commit)
        event.listen(session, "after_commit", after_commit)


class ES:
    def __init__(self, app: Flask | None = None) -> None:
        self.es: Elasticsearch | None = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):

        self.es = Elasticsearch(app.config.get("ES_HOST"))
        app.extensions["es"] = self


es = ES()

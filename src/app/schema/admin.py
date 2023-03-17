from datetime import date

from pydantic import BaseModel, Field, validator

from .common import PageSchema, validate_mobile, validate_password


class AdminLoginSchema(BaseModel):
    mobile: str
    password: str

    _mobile = validator("mobile", allow_reuse=True)(validate_mobile)
    _password = validator("password", allow_reuse=True)(validate_password)


class UserSchema(PageSchema):
    group_id: int | None = None


class UserUpdateSchema(BaseModel):
    group_id: list[int] | None = Field(default=None, min_items=1)


class GroupUpdateSchema(BaseModel):
    name: str
    info: str | None = None


class GroupCreateSchema(GroupUpdateSchema):
    name: str
    info: str | None = None
    permission_ids: list[int] | None = Field(default=None, min_items=1)


class PermissionDispatch(BaseModel):
    group_id: int
    permission_id: int


class PermissionDispatchBatch(BaseModel):
    group_id: int
    permission_ids: list[int] = Field(min_items=1)


class PostSchema(PageSchema):
    category_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_deleted: int | None = None

    @validator(
        "end_date",
        always=True,
    )
    def validate_end_date(cls, v, values, **kwargs):
        # print(v)
        # print(values)
        if v is None:
            if "start_date" in values and values["start_date"] is not None:
                raise ValueError("设置起始时间，必须设置结束时间")
        else:
            if "start_date" not in values or values["start_date"] is None:
                raise ValueError("设置结束时间，必须设置起始时间")
        return v


class PostStatusSchema(BaseModel):
    status: int

    @validator("status")
    def validate_status(cls, v):
        if v > 3 or v < 0:
            raise ValueError("只能是0-3直接的数字")
        return v


class CategoryCreateSchema(BaseModel):
    name: str
    info: str | None = None
    banner: str | None = None
    sort: int | None = 1
    status: int | None = 1


class TagSchema(PageSchema):

    pass


class TagCreateSchema(BaseModel):
    name: str
    color: str
    bg: str


class CommentUpdateSchema(BaseModel):
    type: int  # 1-置顶，2-拉黑
    value: int  # 0-取消，1-设置

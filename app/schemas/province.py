from pydantic import BaseModel, ConfigDict, Field


class ProvinceBase(BaseModel):
    name: str = Field(..., example="Western Province")
    code: str = Field(..., example="WP")


class ProvinceCreate(ProvinceBase):
    pass


class ProvinceResponse(ProvinceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

from app.schemas.error import ErrorResponse
from app.schemas.token import Token, UserLoginRequest, DeviceTokenRequest
from app.schemas.province import ProvinceBase, ProvinceCreate, ProvinceResponse
from app.schemas.district import DistrictBase, DistrictCreate, DistrictResponse
from app.schemas.grid_substation import GridSubstationBase, GridSubstationCreate, GridSubstationResponse
from app.schemas.solar_installation import SolarInstallationBase, SolarInstallationCreate, SolarInstallationResponse, SolarInstallationComposite
from app.schemas.generation_reading import GenerationReadingBase, GenerationReadingCreate, GenerationReadingResponse, PaginatedReadingsResponse
from app.schemas.summary import DistrictGenerationSummary
from app.schemas.user import UserBase, UserCreate, UserResponse

__all__ = [
    "ErrorResponse",
    "Token",
    "UserLoginRequest",
    "DeviceTokenRequest",
    "ProvinceBase",
    "ProvinceCreate",
    "ProvinceResponse",
    "DistrictBase",
    "DistrictCreate",
    "DistrictResponse",
    "GridSubstationBase",
    "GridSubstationCreate",
    "GridSubstationResponse",
    "SolarInstallationBase",
    "SolarInstallationCreate",
    "SolarInstallationResponse",
    "SolarInstallationComposite",
    "GenerationReadingBase",
    "GenerationReadingCreate",
    "GenerationReadingResponse",
    "PaginatedReadingsResponse",
    "DistrictGenerationSummary",
    "UserBase",
    "UserCreate",
    "UserResponse",
]

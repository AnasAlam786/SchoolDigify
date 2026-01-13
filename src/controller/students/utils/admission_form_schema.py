from pydantic import BaseModel, Field, EmailStr, constr, conint, ConfigDict, field_validator, model_validator
from typing import Optional, Literal, Any, get_origin, get_args, Union
from enum import Enum as PyEnum
from .validate_aadhaar import verify_aadhaar
from .str_to_date import str_to_date
from src.model.enums import StudentsDBEnums

# Build Python Enums from SQLAlchemy Enum values
def _sanitize_enum_member_name(raw: str) -> str:
    name = ''.join(ch if ch.isalnum() else '_' for ch in str(raw)).upper()
    if name and name[0].isdigit():
        name = f'N_{name}'
    return name or 'EMPTY'

def _build_python_enum(enum_name: str, sa_enum) -> type[PyEnum]:
    members = {}
    seen = set()
    for value in sa_enum.enums:
        base_name = _sanitize_enum_member_name(value)
        name = base_name
        counter = 1
        while name in seen:
            counter += 1
            name = f"{base_name}_{counter}"
        seen.add(name)
        members[name] = value
    return PyEnum(enum_name, members)

GenderEnum = _build_python_enum("GENDER", StudentsDBEnums.GENDER)
CasteTypeEnum = _build_python_enum("Caste_Type", StudentsDBEnums.CASTE_TYPE)
ReligionEnum = _build_python_enum("RELIGION", StudentsDBEnums.RELIGION)
BloodGroupEnum = _build_python_enum("BLOOD_GROUP", StudentsDBEnums.BLOOD_GROUP)
EducationTypeEnum = _build_python_enum("EDUCATION_TYPE", StudentsDBEnums.EDUCATION_TYPE)
FatherOccupationEnum = _build_python_enum("FATHERS_OCCUPATION", StudentsDBEnums.FATHERS_OCCUPATION)
MotherOccupationEnum = _build_python_enum("MOTHERS_OCCUPATION", StudentsDBEnums.MOTHERS_OCCUPATION)
HomeDistanceEnum = _build_python_enum("Home_Distance", StudentsDBEnums.HOME_DISTANCE)

class CleanBaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, str_to_upper=False)

    @model_validator(mode="before")
    @classmethod
    def clean_data(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(values, dict):
            return values
        cleaned = {}
        for key, value in values.items():
            field_info = cls.model_fields.get(key)
            if not field_info:
                cleaned[key] = value
                continue
            annotation = field_info.annotation
            origin = get_origin(annotation)
            # Skip cleaning for Literal and Enum types
            if origin is Literal or (isinstance(annotation, type) and issubclass(annotation, PyEnum)):
                cleaned[key] = value
                continue
            # Handle Optional Enums
            if origin in (Union, Optional) and any(isinstance(arg, type) and issubclass(arg, PyEnum) for arg in get_args(annotation)):
                if isinstance(value, str) and value.strip() == "":
                    cleaned[key] = None
                else:
                    cleaned[key] = value
                continue
            # Clean strings
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    value = None
                elif not key.lower().endswith("email"):
                    value = value.title()
            cleaned[key] = value
        return cleaned

    def to_verified_data(self) -> list[dict[str, Any]]:
        config_extra = self.__class__.model_config.get("json_schema_extra", {}) or {}
        result = []
        for field_name, field_info in self.model_fields.items():
            value = getattr(self, field_name)
            if isinstance(value, PyEnum):
                value = value.value
            label = config_extra.get(field_name, {}).get("data-short_label", field_name)
            result.append({"field": field_name, "value": value, "label": label})
        return result


# ------------------------- Personal Info -------------------------
class AdmissionFormModel(CleanBaseModel):
    
    STUDENTS_NAME: constr(pattern=r'^[^\W\d_]+(?: [^\W\d_]+)*$') = Field(...) # type: ignore
    
    DOB: str = Field(...)
    GENDER: GenderEnum = Field(...)
    AADHAAR: Optional[constr(min_length=12, max_length=12)] = Field(default=None) # type: ignore
    Caste: Optional[str] = Field(None)
    Caste_Type: CasteTypeEnum = Field(...)

    RELIGION: ReligionEnum = Field(...)

    Height: Optional[conint(gt=0, lt=300)] = Field(None) # type: ignore
    Weight: Optional[conint(gt=0, lt=300)] = Field(None) # type: ignore

    BLOOD_GROUP: Optional[BloodGroupEnum] = Field(None)
        
    # ------------------------- Academic Info -------------------------
    admission_session_id: str = Field(...)
    Admission_Class: str = Field(...)
    CLASS: str = Field(...)
    ROLL: conint(gt=0) = Field(...) # type: ignore
    SR: conint(gt=0) = Field(...) # type: ignore
    ADMISSION_NO: conint(gt=0) = Field(...) # type: ignore
    ADMISSION_DATE: str = Field(...)
    PEN: Optional[constr(max_length=11, min_length=11)] = Field(None) # type: ignore
    APAAR: Optional[constr(max_length=12, min_length=12)] = Field(None) # type: ignore


    
    # ------------------------- Guardian Info -------------------------
    FATHERS_NAME: constr(pattern=r'^[^\W\d_]+(?: [^\W\d_]+)*$') = Field(...) # type: ignore
    FATHERS_AADHAR: Optional[constr(max_length=12, min_length=12)] = Field(None) # type: ignore
    MOTHERS_NAME: constr(pattern=r'^[^\W\d_]+(?: [^\W\d_]+)*$') = Field(...) # type: ignore
    MOTHERS_AADHAR: Optional[constr(max_length=12, min_length=12)] = Field(None) # type: ignore
    
    FATHERS_EDUCATION: Optional[EducationTypeEnum] = Field(None)
    FATHERS_OCCUPATION: Optional[FatherOccupationEnum] = Field(None)
    MOTHERS_EDUCATION: Optional[EducationTypeEnum] = Field(None)
    MOTHERS_OCCUPATION: Optional[MotherOccupationEnum] = Field(None)


    ADDRESS: str = Field(...) # type: ignore
    PHONE: conint(ge=1000000000, le=9999999999) = Field(...) # type: ignore
    ALT_MOBILE: Optional[conint(ge=1000000000, le=9999999999)] = Field(None) # type: ignore
    PIN: conint(ge=100000, le=999999) = Field(...) # type: ignore
    Home_Distance: Optional[HomeDistanceEnum] = Field(default=None)
    EMAIL: Optional[EmailStr] = Field(None)


    Previous_School_Marks: Optional[constr(max_length=3)] = Field(None) # type: ignore
    Previous_School_Attendance: Optional[constr(max_length=3)] = Field(None) # type: ignore
    Previous_School_Name: Optional[constr(min_length=2)] = Field(None) # type: ignore
    Due_Amount: Optional[float] = Field(None)

    # --- RTE fields ---
    is_RTE: bool = Field(default=False)
    account_number: Optional[constr(min_length=9, max_length=18)] = Field(None)
    RTE_registered_year: Optional[conint(gt=2000, lt=2100)] = Field(None)
    ifsc: Optional[constr(min_length=11, max_length=11)] = Field(None)
    bank_name: Optional[str] = Field(None)
    bank_branch: Optional[str] = Field(None)
    account_holder: Optional[str] = Field(None)

    @field_validator('DOB', 'ADMISSION_DATE', mode='before')
    @classmethod
    def date_normalization(cls, v):
        if not v:
            return None
        
        date = str_to_date(v)
        return date
    
    # --- Field validators ---
    @field_validator('AADHAAR', 'FATHERS_AADHAR', 'MOTHERS_AADHAR', mode='before')
    @classmethod
    def clean_aadhaar(cls, v):
        if not v:
            return None
        
        validated_clean_aaadhar = verify_aadhaar(v)
        return validated_clean_aaadhar

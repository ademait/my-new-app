from datetime import datetime, date, time
from typing import Any, List, Optional, Union, Set
from enum import Enum
from pydantic import BaseModel, field_validator

from abc import ABC, abstractmethod

############################################
# Enumerations are defined here
############################################

class EvaluationStatus(Enum):
    Archived = "Archived"
    Custom = "Custom"
    Pending = "Pending"
    Done = "Done"
    Processing = "Processing"

class VerificationType(Enum):
    Case_1 = "Case_1"
    Case_2 = "Case_2"
    Case_3 = "Case_3"

class TagsVerificationTarget(Enum):
    Technical_Robustness__and_Saftey = "Technical_Robustness__and_Saftey"
    Societal_and_enviornmanetal_wellbeing = "Societal_and_enviornmanetal_wellbeing"
    Privacy_and_Data_Governance = "Privacy_and_Data_Governance"
    Diversity_Nondiscrimination_and_Fairness = "Diversity_Nondiscrimination_and_Fairness"
    Transparency = "Transparency"
    Accountability = "Accountability"
    Human_Agency_and_Oversight = "Human_Agency_and_Oversight"
    Risk_management = "Risk_management"

class LicensingType(Enum):
    Proprietary = "Proprietary"
    Open_Source = "Open_Source"

class TagsTargetSystem(Enum):
    Emerging_Other = "Emerging_Other"
    AI_Safety_and_Governance = "AI_Safety_and_Governance"
    Natural_Language_Processing = "Natural_Language_Processing"
    Knowledge_and_Retrival = "Knowledge_and_Retrival"
    Decision_and_Optimization = "Decision_and_Optimization"
    Predictive_and_Analytical_AI = "Predictive_and_Analytical_AI"
    Recommendation_and_Personalization = "Recommendation_and_Personalization"
    Tabular_and_Structured_Data = "Tabular_and_Structured_Data"
    Computer_Vision = "Computer_Vision"
    Reinforcement_Learning_and_Control = "Reinforcement_Learning_and_Control"
    Multimodal = "Multimodal"
    Audio = "Audio"
    Agents_and_Agentic_Systems = "Agents_and_Agentic_Systems"

class ProjectStatus(Enum):
    Created = "Created"
    Pending = "Pending"
    Ready = "Ready"
    Closed = "Closed"
    Archived = "Archived"

class DatasetType(Enum):
    Validation = "Validation"
    Training = "Training"
    Test = "Test"

class TagsSector(Enum):
    Education = "Education"
    Investment = "Investment"
    Innovation = "Innovation"
    Inclusive_development = "Inclusive_development"
    Agriculture = "Agriculture"
    Competition = "Competition"
    Health = "Health"
    Defence = "Defence"
    Trade = "Trade"
    Environment = "Environment"
    Economz = "Economz"

############################################
# Classes are defined here
############################################
class UserCreate(BaseModel):
    name: str
    tool: Optional[int] = None  # N:1 Relationship (optional)


class LegalRequirementCreate(BaseModel):
    legal_ref: str
    principle: str
    standard: str
    project_1: int  # N:1 Relationship (mandatory)


class AssessmentElementCreate(ABC, BaseModel):
    name: str
    description: str


class MetricCreate(AssessmentElementCreate):
    derivedBy: Optional[List[int]] = None  # N:M Relationship (optional)
    category: Optional[List[int]] = None  # N:M Relationship (optional)
    measures: Optional[List[int]] = None  # 1:N Relationship


class ToolCreate(AssessmentElementCreate):
    target_legal_requirements: str
    project: str
    branch: str
    provider: str
    licensing: LicensingType
    sector: TagsSector
    target_system: TagsTargetSystem
    verification_targets: TagsVerificationTarget
    scientific_reference: str
    verification_type: VerificationType
    version: str
    project_maturity: str
    observation_1: Optional[List[int]] = None  # 1:N Relationship
    users: Optional[List[int]] = None  # 1:N Relationship


class MetricCategoryCreate(AssessmentElementCreate):
    metrics: Optional[List[int]] = None  # N:M Relationship (optional)


class ConfParamCreate(AssessmentElementCreate):
    value: str
    param_type: str
    conf: int  # N:1 Relationship (mandatory)


class ConfigurationCreate(AssessmentElementCreate):
    params: Optional[List[int]] = None  # 1:N Relationship
    eval: Optional[List[int]] = None  # 1:N Relationship


class DatashapeCreate(BaseModel):
    accepted_target_values: str
    f_date: Optional[List[int]] = None  # N:M Relationship (optional)
    f_features: Optional[List[int]] = None  # 1:N Relationship
    dataset_1: Optional[List[int]] = None  # 1:N Relationship


class ProjectCreate(BaseModel):
    name: str
    status: ProjectStatus
    eval: Optional[List[int]] = None  # 1:N Relationship
    legal_requirements: Optional[List[int]] = None  # 1:N Relationship
    involves: Optional[List[int]] = None  # 1:N Relationship


class DerivedCreate(MetricCreate):
    expression: str
    baseMetric: List[int]  # N:M Relationship


class DirectCreate(MetricCreate):
    pass


class EvaluationCreate(BaseModel):
    status: EvaluationStatus
    project: int  # N:1 Relationship (mandatory)
    evaluates: int  # N:1 Relationship (mandatory)
    observations: Optional[List[int]] = None  # 1:N Relationship
    ref: Optional[List[int]] = None  # N:M Relationship (optional)
    config: int  # N:1 Relationship (mandatory)


class ObservationCreate(AssessmentElementCreate):
    observer: str
    whenObserved: datetime
    eval: int  # N:1 Relationship (mandatory)
    tool: int  # N:1 Relationship (mandatory)
    measures: Optional[List[int]] = None  # 1:N Relationship
    dataset: int  # N:1 Relationship (mandatory)


class MeasureCreate(BaseModel):
    unit: str
    value: str
    error: str
    uncertainty: float
    measurand: int  # N:1 Relationship (mandatory)
    observation: int  # N:1 Relationship (mandatory)
    metric: int  # N:1 Relationship (mandatory)


class ElementCreate(AssessmentElementCreate):
    measure: Optional[List[int]] = None  # 1:N Relationship
    eval: Optional[List[int]] = None  # N:M Relationship (optional)
    project: Optional[int] = None  # N:1 Relationship (optional)
    evalu: Optional[List[int]] = None  # 1:N Relationship


class DatasetCreate(ElementCreate):
    source: str
    licensing: LicensingType
    version: str
    dataset_type: DatasetType
    models: Optional[List[int]] = None  # N:M Relationship (optional)
    observation_2: Optional[List[int]] = None  # 1:N Relationship
    datashape: int  # N:1 Relationship (mandatory)


class FeatureCreate(ElementCreate):
    max_value: float
    feature_type: str
    min_value: float
    date: Optional[List[int]] = None  # N:M Relationship (optional)
    features: int  # N:1 Relationship (mandatory)


class AISystemCreate(ElementCreate):
    settings: str
    version: str
    licensing: LicensingType
    source: str
    data: str
    dataset: List[int]  # N:M Relationship



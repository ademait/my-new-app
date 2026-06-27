import enum
from typing import List as List_, Optional as Optional_
from sqlalchemy import (
    create_engine, Column as Column_, ForeignKey as ForeignKey_, Table as Table_, 
    Text as Text_, Boolean as Boolean_, String as String_, Date as Date_, 
    Time as Time_, DateTime as DateTime_, Float as Float_, Integer as Integer_, Enum
)
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import (
    column_property, DeclarativeBase, Mapped as Mapped_, mapped_column, relationship
)
from datetime import datetime as dt_datetime, time as dt_time, date as dt_date

class Base(DeclarativeBase):
    pass

# Definitions of Enumerations
class EvaluationStatus(enum.Enum):
    Archived = "Archived"
    Custom = "Custom"
    Pending = "Pending"
    Done = "Done"
    Processing = "Processing"

class VerificationType(enum.Enum):
    Case_1 = "Case_1"
    Case_2 = "Case_2"
    Case_3 = "Case_3"

class TagsVerificationTarget(enum.Enum):
    Technical_Robustness__and_Saftey = "Technical_Robustness__and_Saftey"
    Societal_and_enviornmanetal_wellbeing = "Societal_and_enviornmanetal_wellbeing"
    Privacy_and_Data_Governance = "Privacy_and_Data_Governance"
    Diversity_Nondiscrimination_and_Fairness = "Diversity_Nondiscrimination_and_Fairness"
    Transparency = "Transparency"
    Accountability = "Accountability"
    Human_Agency_and_Oversight = "Human_Agency_and_Oversight"
    Risk_management = "Risk_management"

class LicensingType(enum.Enum):
    Proprietary = "Proprietary"
    Open_Source = "Open_Source"

class TagsTargetSystem(enum.Enum):
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

class ProjectStatus(enum.Enum):
    Created = "Created"
    Pending = "Pending"
    Ready = "Ready"
    Closed = "Closed"
    Archived = "Archived"

class DatasetType(enum.Enum):
    Validation = "Validation"
    Training = "Training"
    Test = "Test"

class TagsSector(enum.Enum):
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


# Tables definition for many-to-many relationships
derived_metric = Table_(
    "derived_metric",
    Base.metadata,
    Column_("baseMetric", ForeignKey_("metric.id"), primary_key=True),
    Column_("derivedBy", ForeignKey_("derived.id"), primary_key=True),
)
evaluation_element = Table_(
    "evaluation_element",
    Base.metadata,
    Column_("ref", ForeignKey_("element.id"), primary_key=True),
    Column_("eval", ForeignKey_("evaluation.id"), primary_key=True),
)
datashape_feature = Table_(
    "datashape_feature",
    Base.metadata,
    Column_("f_date", ForeignKey_("feature.id"), primary_key=True),
    Column_("date", ForeignKey_("datashape.id"), primary_key=True),
)
aisystem_dataset = Table_(
    "aisystem_dataset",
    Base.metadata,
    Column_("dataset", ForeignKey_("dataset.id"), primary_key=True),
    Column_("models", ForeignKey_("aisystem.id"), primary_key=True),
)
metriccategory_metric = Table_(
    "metriccategory_metric",
    Base.metadata,
    Column_("metrics", ForeignKey_("metric.id"), primary_key=True),
    Column_("category", ForeignKey_("metriccategory.id"), primary_key=True),
)

# Tables definition
class User(Base):
    __tablename__ = "user"
    id: Mapped_[int] = mapped_column(primary_key=True)
    name: Mapped_[str] = mapped_column(String_(100))
    tool_id: Mapped_[int] = mapped_column(ForeignKey_("tool.id"), nullable=True)

class LegalRequirement(Base):
    __tablename__ = "legalrequirement"
    id: Mapped_[int] = mapped_column(primary_key=True)
    legal_ref: Mapped_[str] = mapped_column(String_(100))
    standard: Mapped_[str] = mapped_column(String_(100))
    principle: Mapped_[str] = mapped_column(String_(100))
    project_1_id: Mapped_[int] = mapped_column(ForeignKey_("project.id"))

class AssessmentElement(AbstractConcreteBase, Base):
    strict_attrs = True
    id: Mapped_[int] = mapped_column(primary_key=True)
    name: Mapped_[str] = mapped_column(String_(100))
    description: Mapped_[str] = mapped_column(String_(100))

class Metric(AssessmentElement):
    __tablename__ = "metric"
    id: Mapped_[int] = mapped_column(primary_key=True)
    type_spec: Mapped_[str] = mapped_column(String_(50))
    __mapper_args__ = {
        "polymorphic_identity": "metric",
        "polymorphic_on": "type_spec",
    }

class Tool(AssessmentElement):
    __tablename__ = "tool"
    id: Mapped_[int] = mapped_column(primary_key=True)
    licensing: Mapped_[LicensingType] = mapped_column(Enum(LicensingType))
    verification_type: Mapped_[VerificationType] = mapped_column(Enum(VerificationType))
    provider: Mapped_[str] = mapped_column(String_(100))
    project: Mapped_[str] = mapped_column(String_(100))
    branch: Mapped_[str] = mapped_column(String_(100))
    version: Mapped_[str] = mapped_column(String_(100))
    project_maturity: Mapped_[str] = mapped_column(String_(100))
    scientific_reference: Mapped_[str] = mapped_column(String_(100))
    verification_targets: Mapped_[TagsVerificationTarget] = mapped_column(Enum(TagsVerificationTarget))
    sector: Mapped_[TagsSector] = mapped_column(Enum(TagsSector))
    target_system: Mapped_[TagsTargetSystem] = mapped_column(Enum(TagsTargetSystem))
    target_legal_requirements: Mapped_[str] = mapped_column(String_(100))
    __mapper_args__ = {
        "polymorphic_identity": "tool",
        "concrete": True,
    }

class MetricCategory(AssessmentElement):
    __tablename__ = "metriccategory"
    id: Mapped_[int] = mapped_column(primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "metriccategory",
        "concrete": True,
    }

class ConfParam(AssessmentElement):
    __tablename__ = "confparam"
    id: Mapped_[int] = mapped_column(primary_key=True)
    param_type: Mapped_[str] = mapped_column(String_(100))
    value: Mapped_[str] = mapped_column(String_(100))
    conf_id: Mapped_[int] = mapped_column(ForeignKey_("configuration.id"))
    __mapper_args__ = {
        "polymorphic_identity": "confparam",
        "concrete": True,
    }

class Configuration(AssessmentElement):
    __tablename__ = "configuration"
    id: Mapped_[int] = mapped_column(primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "configuration",
        "concrete": True,
    }

class Datashape(Base):
    __tablename__ = "datashape"
    id: Mapped_[int] = mapped_column(primary_key=True)
    accepted_target_values: Mapped_[str] = mapped_column(String_(100))

class Project(Base):
    __tablename__ = "project"
    id: Mapped_[int] = mapped_column(primary_key=True)
    name: Mapped_[str] = mapped_column(String_(100))
    status: Mapped_[ProjectStatus] = mapped_column(Enum(ProjectStatus))

class Derived(Metric):
    __tablename__ = "derived"
    id: Mapped_[int] = mapped_column(ForeignKey_("metric.id"), primary_key=True)
    expression: Mapped_[str] = mapped_column(String_(100))
    __mapper_args__ = {
        "polymorphic_identity": "derived",
    }

class Direct(Metric):
    __tablename__ = "direct"
    id: Mapped_[int] = mapped_column(ForeignKey_("metric.id"), primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "direct",
    }

class Evaluation(Base):
    __tablename__ = "evaluation"
    id: Mapped_[int] = mapped_column(primary_key=True)
    status: Mapped_[EvaluationStatus] = mapped_column(Enum(EvaluationStatus))
    project_id: Mapped_[int] = mapped_column(ForeignKey_("project.id"))
    config_id: Mapped_[int] = mapped_column(ForeignKey_("configuration.id"))
    evaluates_id: Mapped_[int] = mapped_column(ForeignKey_("element.id"))

class Observation(AssessmentElement):
    __tablename__ = "observation"
    id: Mapped_[int] = mapped_column(primary_key=True)
    observer: Mapped_[str] = mapped_column(String_(100))
    whenObserved: Mapped_[dt_datetime] = mapped_column(DateTime_)
    dataset_id: Mapped_[int] = mapped_column(ForeignKey_("dataset.id"))
    eval_id: Mapped_[int] = mapped_column(ForeignKey_("evaluation.id"))
    tool_id: Mapped_[int] = mapped_column(ForeignKey_("tool.id"))
    __mapper_args__ = {
        "polymorphic_identity": "observation",
        "concrete": True,
    }

class Measure(Base):
    __tablename__ = "measure"
    id: Mapped_[int] = mapped_column(primary_key=True)
    value: Mapped_[str] = mapped_column(String_(100))
    error: Mapped_[str] = mapped_column(String_(100))
    uncertainty: Mapped_[float] = mapped_column(Float_)
    unit: Mapped_[str] = mapped_column(String_(100))
    measurand_id: Mapped_[int] = mapped_column(ForeignKey_("element.id"))
    observation_id: Mapped_[int] = mapped_column(ForeignKey_("observation.id"))
    metric_id: Mapped_[int] = mapped_column(ForeignKey_("metric.id"))

class Element(AssessmentElement):
    __tablename__ = "element"
    id: Mapped_[int] = mapped_column(primary_key=True)
    project_id: Mapped_[int] = mapped_column(ForeignKey_("project.id"), nullable=True)
    type_spec: Mapped_[str] = mapped_column(String_(50))
    __mapper_args__ = {
        "polymorphic_identity": "element",
        "polymorphic_on": "type_spec",
    }

class Dataset(Element):
    __tablename__ = "dataset"
    id: Mapped_[int] = mapped_column(ForeignKey_("element.id"), primary_key=True)
    source: Mapped_[str] = mapped_column(String_(100))
    version: Mapped_[str] = mapped_column(String_(100))
    licensing: Mapped_[LicensingType] = mapped_column(Enum(LicensingType))
    dataset_type: Mapped_[DatasetType] = mapped_column(Enum(DatasetType))
    datashape_id: Mapped_[int] = mapped_column(ForeignKey_("datashape.id"))
    __mapper_args__ = {
        "polymorphic_identity": "dataset",
    }

class Feature(Element):
    __tablename__ = "feature"
    id: Mapped_[int] = mapped_column(ForeignKey_("element.id"), primary_key=True)
    max_value: Mapped_[float] = mapped_column(Float_)
    feature_type: Mapped_[str] = mapped_column(String_(100))
    min_value: Mapped_[float] = mapped_column(Float_)
    features_id: Mapped_[int] = mapped_column(ForeignKey_("datashape.id"))
    __mapper_args__ = {
        "polymorphic_identity": "feature",
    }

class AISystem(Element):
    __tablename__ = "aisystem"
    id: Mapped_[int] = mapped_column(ForeignKey_("element.id"), primary_key=True)
    settings: Mapped_[str] = mapped_column(String_(100))
    data: Mapped_[str] = mapped_column(String_(100))
    source: Mapped_[str] = mapped_column(String_(100))
    licensing: Mapped_[LicensingType] = mapped_column(Enum(LicensingType))
    version: Mapped_[str] = mapped_column(String_(100))
    __mapper_args__ = {
        "polymorphic_identity": "aisystem",
    }


#--- Relationships of the user table
User.tool: Mapped_["Tool"] = relationship("Tool", back_populates="users", foreign_keys=[User.tool_id])

#--- Relationships of the legalrequirement table
LegalRequirement.project_1: Mapped_["Project"] = relationship("Project", back_populates="legal_requirements", foreign_keys=[LegalRequirement.project_1_id])

#--- Relationships of the metric table
Metric.measures: Mapped_[List_["Measure"]] = relationship("Measure", back_populates="metric", foreign_keys=[Measure.metric_id])
Metric.derivedBy: Mapped_[List_["Derived"]] = relationship("Derived", secondary=derived_metric, back_populates="baseMetric")
Metric.category: Mapped_[List_["MetricCategory"]] = relationship("MetricCategory", secondary=metriccategory_metric, back_populates="metrics")

#--- Relationships of the tool table
Tool.users: Mapped_[List_["User"]] = relationship("User", back_populates="tool", foreign_keys=[User.tool_id])
Tool.observation_1: Mapped_[List_["Observation"]] = relationship("Observation", back_populates="tool", foreign_keys=[Observation.tool_id])

#--- Relationships of the metriccategory table
MetricCategory.metrics: Mapped_[List_["Metric"]] = relationship("Metric", secondary=metriccategory_metric, back_populates="category")

#--- Relationships of the confparam table
ConfParam.conf: Mapped_["Configuration"] = relationship("Configuration", back_populates="params", foreign_keys=[ConfParam.conf_id])

#--- Relationships of the configuration table
Configuration.params: Mapped_[List_["ConfParam"]] = relationship("ConfParam", back_populates="conf", foreign_keys=[ConfParam.conf_id])
Configuration.eval: Mapped_[List_["Evaluation"]] = relationship("Evaluation", back_populates="config", foreign_keys=[Evaluation.config_id])

#--- Relationships of the datashape table
Datashape.f_date: Mapped_[List_["Feature"]] = relationship("Feature", secondary=datashape_feature, back_populates="date")
Datashape.f_features: Mapped_[List_["Feature"]] = relationship("Feature", back_populates="features", foreign_keys=[Feature.features_id])
Datashape.dataset_1: Mapped_[List_["Dataset"]] = relationship("Dataset", back_populates="datashape", foreign_keys=[Dataset.datashape_id])

#--- Relationships of the project table
Project.legal_requirements: Mapped_[List_["LegalRequirement"]] = relationship("LegalRequirement", back_populates="project_1", foreign_keys=[LegalRequirement.project_1_id])
Project.involves: Mapped_[List_["Element"]] = relationship("Element", back_populates="project", foreign_keys=[Element.project_id])
Project.eval: Mapped_[List_["Evaluation"]] = relationship("Evaluation", back_populates="project", foreign_keys=[Evaluation.project_id])

#--- Relationships of the derived table
Derived.baseMetric: Mapped_[List_["Metric"]] = relationship("Metric", secondary=derived_metric, back_populates="derivedBy")

#--- Relationships of the evaluation table
Evaluation.observations: Mapped_[List_["Observation"]] = relationship("Observation", back_populates="eval", foreign_keys=[Observation.eval_id])
Evaluation.project: Mapped_["Project"] = relationship("Project", back_populates="eval", foreign_keys=[Evaluation.project_id])
Evaluation.config: Mapped_["Configuration"] = relationship("Configuration", back_populates="eval", foreign_keys=[Evaluation.config_id])
Evaluation.evaluates: Mapped_["Element"] = relationship("Element", back_populates="evalu", foreign_keys=[Evaluation.evaluates_id])
Evaluation.ref: Mapped_[List_["Element"]] = relationship("Element", secondary=evaluation_element, back_populates="eval")

#--- Relationships of the observation table
Observation.dataset: Mapped_["Dataset"] = relationship("Dataset", back_populates="observation_2", foreign_keys=[Observation.dataset_id])
Observation.eval: Mapped_["Evaluation"] = relationship("Evaluation", back_populates="observations", foreign_keys=[Observation.eval_id])
Observation.tool: Mapped_["Tool"] = relationship("Tool", back_populates="observation_1", foreign_keys=[Observation.tool_id])
Observation.measures: Mapped_[List_["Measure"]] = relationship("Measure", back_populates="observation", foreign_keys=[Measure.observation_id])

#--- Relationships of the measure table
Measure.measurand: Mapped_["Element"] = relationship("Element", back_populates="measure", foreign_keys=[Measure.measurand_id])
Measure.observation: Mapped_["Observation"] = relationship("Observation", back_populates="measures", foreign_keys=[Measure.observation_id])
Measure.metric: Mapped_["Metric"] = relationship("Metric", back_populates="measures", foreign_keys=[Measure.metric_id])

#--- Relationships of the element table
Element.project: Mapped_["Project"] = relationship("Project", back_populates="involves", foreign_keys=[Element.project_id])
Element.evalu: Mapped_[List_["Evaluation"]] = relationship("Evaluation", back_populates="evaluates", foreign_keys=[Evaluation.evaluates_id])
Element.measure: Mapped_[List_["Measure"]] = relationship("Measure", back_populates="measurand", foreign_keys=[Measure.measurand_id])
Element.eval: Mapped_[List_["Evaluation"]] = relationship("Evaluation", secondary=evaluation_element, back_populates="ref")

#--- Relationships of the dataset table
Dataset.models: Mapped_[List_["AISystem"]] = relationship("AISystem", secondary=aisystem_dataset, back_populates="dataset")
Dataset.datashape: Mapped_["Datashape"] = relationship("Datashape", back_populates="dataset_1", foreign_keys=[Dataset.datashape_id])
Dataset.observation_2: Mapped_[List_["Observation"]] = relationship("Observation", back_populates="dataset", foreign_keys=[Observation.dataset_id])

#--- Relationships of the feature table
Feature.features: Mapped_["Datashape"] = relationship("Datashape", back_populates="f_features", foreign_keys=[Feature.features_id])
Feature.date: Mapped_[List_["Datashape"]] = relationship("Datashape", secondary=datashape_feature, back_populates="f_date")

#--- Relationships of the aisystem table
AISystem.dataset: Mapped_[List_["Dataset"]] = relationship("Dataset", secondary=aisystem_dataset, back_populates="models")

# Database connection
DATABASE_URL = "sqlite:///AI_Sandbox.db"  # SQLite connection
engine = create_engine(DATABASE_URL, echo=True)

# Create tables in the database
Base.metadata.create_all(engine, checkfirst=True)
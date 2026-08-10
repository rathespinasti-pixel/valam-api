from datetime import datetime

from app.extensions import db


class ManagedCrop(db.Model):
    __tablename__ = "managed_crops"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    scientific_name = db.Column(db.String(160))
    category = db.Column(db.String(80))
    description = db.Column(db.Text)
    suitable_regions = db.Column(db.JSON, default=list)
    suitable_seasons = db.Column(db.JSON, default=list)
    status = db.Column(db.String(20), nullable=False, default="draft", index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lifecycle_stages = db.relationship("CropLifecycleStage", cascade="all, delete-orphan", backref="crop", lazy=True)
    planting_methods = db.relationship("PlantingMethod", cascade="all, delete-orphan", backref="crop", lazy=True)
    soil_requirements = db.relationship("SoilRequirement", cascade="all, delete-orphan", backref="crop", lazy=True)
    composts = db.relationship("Compost", cascade="all, delete-orphan", backref="crop", lazy=True)
    fertilizers = db.relationship("Fertilizer", cascade="all, delete-orphan", backref="crop", lazy=True)
    irrigations = db.relationship("Irrigation", cascade="all, delete-orphan", backref="crop", lazy=True)
    pests = db.relationship("Pest", cascade="all, delete-orphan", backref="crop", lazy=True)
    diseases = db.relationship("CropDisease", cascade="all, delete-orphan", backref="crop", lazy=True)
    harvest_information = db.relationship("HarvestInformation", cascade="all, delete-orphan", backref="crop", uselist=False)

    def to_dict(self, detailed=True):
        data = {"id": self.id, "name": self.name, "scientific_name": self.scientific_name,
                "category": self.category, "description": self.description,
                "suitable_regions": self.suitable_regions or [], "suitable_seasons": self.suitable_seasons or [],
                "status": self.status, "created_by": self.created_by, "updated_by": self.updated_by,
                "created_at": self.created_at.isoformat(), "updated_at": self.updated_at.isoformat()}
        if detailed:
            data.update({
                "lifecycle_stages": [x.to_dict() for x in sorted(self.lifecycle_stages, key=lambda x: x.stage_order)],
                "planting_methods": [x.to_dict() for x in self.planting_methods],
                "soil_requirements": [x.to_dict() for x in self.soil_requirements],
                "composts": [x.to_dict() for x in self.composts], "fertilizers": [x.to_dict() for x in self.fertilizers],
                "irrigations": [x.to_dict() for x in self.irrigations], "pests": [x.to_dict() for x in self.pests],
                "diseases": [x.to_dict() for x in self.diseases],
                "harvest_information": self.harvest_information.to_dict() if self.harvest_information else None,
            })
        return data


class SectionBase:
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey("managed_crops.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in ("crop_id",)} | {
            "created_at": self.created_at.isoformat(), "updated_at": self.updated_at.isoformat()}


class CropLifecycleStage(SectionBase, db.Model):
    __tablename__ = "managed_crop_lifecycle_stages"
    stage_name = db.Column(db.String(120), nullable=False)
    stage_order = db.Column(db.Integer, nullable=False, default=1)
    start_day = db.Column(db.Integer)
    end_day = db.Column(db.Integer)
    duration = db.Column(db.Integer)
    description = db.Column(db.Text)
    recommended_activities = db.Column(db.JSON, default=list)
    image_url = db.Column(db.Text)
    image_source = db.Column(db.String(30))
    image_approved = db.Column(db.Boolean, default=False, nullable=False)


class PlantingMethod(SectionBase, db.Model):
    __tablename__ = "managed_crop_planting_methods"
    planting_method = db.Column(db.String(120)); method_type = db.Column(db.String(80)); seed_quantity = db.Column(db.String(120))
    planting_depth = db.Column(db.String(120)); plant_spacing = db.Column(db.String(120)); row_spacing = db.Column(db.String(120))
    nursery_duration = db.Column(db.String(120)); transplanting_information = db.Column(db.Text)
    recommended_season = db.Column(db.String(160)); additional_instructions = db.Column(db.Text)


class SoilRequirement(SectionBase, db.Model):
    __tablename__ = "managed_crop_soil_requirements"
    soil_type = db.Column(db.String(160)); recommended_ph = db.Column(db.String(80)); drainage_requirement = db.Column(db.Text)
    soil_preparation = db.Column(db.Text); organic_matter_requirements = db.Column(db.Text); land_preparation_instructions = db.Column(db.Text)


class Compost(SectionBase, db.Model):
    __tablename__ = "managed_crop_composts"
    compost_type = db.Column(db.String(160)); quantity = db.Column(db.String(120)); organic_manure = db.Column(db.Text)
    organic_alternatives = db.Column(db.Text); additional_instructions = db.Column(db.Text)


class Fertilizer(SectionBase, db.Model):
    __tablename__ = "managed_crop_fertilizers"
    name = db.Column(db.String(160)); fertilizer_type = db.Column(db.String(100)); npk_ratio = db.Column(db.String(80))
    application_quantity = db.Column(db.String(120)); application_method = db.Column(db.Text); application_stage = db.Column(db.String(120))
    application_frequency = db.Column(db.String(120)); organic_alternatives = db.Column(db.Text); additional_instructions = db.Column(db.Text)


class Irrigation(SectionBase, db.Model):
    __tablename__ = "managed_crop_irrigations"
    method = db.Column(db.String(120)); water_requirement = db.Column(db.String(160)); frequency = db.Column(db.String(120))
    water_quantity = db.Column(db.String(120)); duration = db.Column(db.String(120)); stage_recommendations = db.Column(db.JSON, default=list)
    special_instructions = db.Column(db.Text)


class Pest(SectionBase, db.Model):
    __tablename__ = "managed_crop_pests"
    name = db.Column(db.String(160)); symptoms = db.Column(db.Text); causes = db.Column(db.Text); prevention = db.Column(db.Text)
    treatment = db.Column(db.Text); organic_treatment = db.Column(db.Text); recommended_action = db.Column(db.Text); lifecycle_stage_affected = db.Column(db.String(120))


class CropDisease(SectionBase, db.Model):
    __tablename__ = "managed_crop_diseases"
    name = db.Column(db.String(160)); symptoms = db.Column(db.Text); causes = db.Column(db.Text); prevention = db.Column(db.Text)
    treatment = db.Column(db.Text); organic_treatment = db.Column(db.Text); recommended_action = db.Column(db.Text); lifecycle_stage_affected = db.Column(db.String(120))


class HarvestInformation(SectionBase, db.Model):
    __tablename__ = "managed_crop_harvest_information"
    expected_harvest_days = db.Column(db.String(120)); harvest_indicators = db.Column(db.Text); harvest_method = db.Column(db.Text)
    harvest_frequency = db.Column(db.String(120)); expected_yield = db.Column(db.String(120)); storage_information = db.Column(db.Text)
    post_harvest_instructions = db.Column(db.Text)

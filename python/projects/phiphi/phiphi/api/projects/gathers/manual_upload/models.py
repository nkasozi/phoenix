"""Manual upload gather model."""

import sqlalchemy as sa

from phiphi.api.projects.gathers import models as gather_models


class ManualUploadGather(gather_models.Gather):
    """Apify Gather model."""

    __tablename__ = "manual_upload_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "manual_upload",
    }

    id: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.ForeignKey("gathers.id"), primary_key=True)
    uploaded_file_name: sa.orm.Mapped[str]
    file_url: sa.orm.Mapped[str]
    file_size: sa.orm.Mapped[int]
    file_row_count: sa.orm.Mapped[int]

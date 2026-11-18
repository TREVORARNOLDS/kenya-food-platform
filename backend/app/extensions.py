from flask_cors import CORS
from flask_migrate import Migrate
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy

# Tables owned by PostGIS extensions. Alembic must never manage them.
POSTGIS_TABLES = {"spatial_ref_sys", "geometry_columns", "geography_columns"}


def include_object(obj, name, type_, reflected, compare_to):
    return not (type_ == "table" and name in POSTGIS_TABLES)


db = SQLAlchemy()
migrate = Migrate()
smorest_api = Api()
cors = CORS()
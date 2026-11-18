def register_blueprints(smorest_api) -> None:
    from .commodities.routes import blp as commodities_blp
    from .geography.routes import blp as geography_blp
    from .health.routes import blp as health_blp
    from .markets.routes import blp as markets_blp
    from .prices.routes import blp as prices_blp

    for blp in (health_blp, geography_blp, markets_blp, commodities_blp, prices_blp):
        smorest_api.register_blueprint(blp)

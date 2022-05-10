from starlette.config import Config

config = Config(".env")

GMAPS_KEY = config("GMAPS_KEY")
DEBUG = config("DEBUG", cast=bool, default=False)

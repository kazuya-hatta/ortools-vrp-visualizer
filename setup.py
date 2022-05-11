from setuptools import setup

setup(
    name="ortools_viz_backend",
    version="0.0.1",
    packages=["ortools_viz_backend"],
    install_requires=[
        "starlette==0.19.1",
        "uvicorn==0.17.6",
        "ortools==9.3.10497",
        "jinja2==3.1.2",
        "httpx==0.22.0",
        "googlemaps==4.6.0",
        "pytest",
        "requests",
        "mypy",
    ],
)

import setuptools
from version import get_version

VERSION = get_version()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

setuptools.setup(
    name="csctracker-py-core",
    version=VERSION,
    license="MIT",
    author="Carlos Eduardo",
    description="A base library for microservices with Flask, JSON logging, and Prometheus telemetry.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/krlsedu/CscTrackerPyCore",
    project_urls={
        "Bug Tracker": "https://github.com/krlsedu/CscTrackerPyCore/issues",
        "Source Code": "https://github.com/krlsedu/CscTrackerPyCore",
    },
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    keywords=[
        "microservices",
        "flask",
        "json-logging",
        "prometheus",
        "telemetry",
        "swagger",
        "openapi",
        "background-jobs",
        "scheduler",
        "observability",
        "http-client",
        "middleware"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    install_requires=required,
    python_requires=">=3.9",
    include_package_data=True,
)
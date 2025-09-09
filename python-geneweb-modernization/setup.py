"""
GenEWeb Python Modernization Setup Script

This script sets up the Python modernization of GenEWeb,
maintaining compatibility with existing databases while
providing modern Python infrastructure.
"""

from setuptools import setup, find_packages
import os

# Read long description from README
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# Read version from package
def read_version():
    version_file = os.path.join("geneweb", "__init__.py")
    with open(version_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"

setup(
    name="geneweb-python",
    version=read_version(),
    author="GenEWeb Python Modernization Project",
    author_email="contact@geneweb.org",
    description="Python modernization of GenEWeb genealogical software",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/geneweb/geneweb",
    project_urls={
        "Bug Tracker": "https://github.com/geneweb/geneweb/issues",
        "Documentation": "https://geneweb.tuxfamily.org/wiki/GeneWeb",
        "Source Code": "https://github.com/geneweb/geneweb",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Sociology :: Genealogy",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies
        "aiofiles>=0.8.0",
        "aiohttp>=3.8.0",
        "click>=8.0.0",
        
        # Date and time handling
        "python-dateutil>=2.8.0",
        
        # Template engine
        "jinja2>=3.0.0",
        
        # Configuration
        "pyyaml>=6.0",
        "toml>=0.10.0",
        
        # Cryptography for security
        "cryptography>=3.4.0",
        
        # Database support
        "sqlalchemy>=1.4.0",
        
        # Web framework utilities
        "werkzeug>=2.0.0",
        
        # File format support
        "lxml>=4.6.0",  # For XML/GEDCOM processing
        "pillow>=8.0.0",  # For image handling
        
        # Internationalization
        "babel>=2.9.0",
        
        # Utilities
        "colorama>=0.4.0",  # For colored console output
        "tqdm>=4.60.0",  # For progress bars
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.900",
            "pre-commit>=2.15.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
        "performance": [
            "ujson>=5.0.0",
            "orjson>=3.6.0",
            "uvloop>=0.16.0",  # Faster event loop for asyncio
        ],
        "database": [
            "psycopg2-binary>=2.9.0",  # PostgreSQL support
            "mysql-connector-python>=8.0.0",  # MySQL support
            "redis>=4.0.0",  # Redis for caching
        ],
    },
    entry_points={
        "console_scripts": [
            "geneweb=geneweb.cli:main",
            "geneweb-server=geneweb.web.server:main",
            "geneweb-import=geneweb.tools.import_data:main",
            "geneweb-export=geneweb.tools.export_data:main",
        ],
    },
    package_data={
        "geneweb": [
            "templates/*.html",
            "templates/*.txt",
            "static/css/*.css",
            "static/js/*.js",
            "static/images/*",
            "locale/*/*.po",
            "locale/*/*.mo",
            "data/*.txt",
            "data/*.json",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "genealogy", "family tree", "ancestry", "geneweb", 
        "database", "web server", "historical", "preservation"
    ],
    platforms=["any"],
)

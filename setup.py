import os

from setuptools import find_packages, setup

VERSION = "0.2.1b2"


def get_readme() -> str:
    """Load the contents of the README file"""
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    with open(readme_path, "r") as f:
        return f.read()


setup(
    name="orm_converter",
    description="A utility that allows you to convert ORM models.",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    version=VERSION,
    packages=find_packages(include=["orm_converter", "orm_converter.*"]),
    url="https://github.com/MaximZayats/orm-converter",
    license="MIT",
    author="Maxim",
    install_requires=["tortoise-orm~=0.17.6", "Django~=3.2.6"],
    author_email="maximzayats1@gmail.com",
    keywords=[
        "python",
        "django",
        "orm",
        "conversion",
        "orm-framework",
        "tortoise-orm",
        "django-orm",
        "admin-panel",
    ],
)

from setuptools import setup, find_packages
setup(
    name="project_name",
    version="0.1",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "project-name=project_name.core:main"
        ]
    }
)

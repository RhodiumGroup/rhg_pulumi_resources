from setuptools import setup, find_packages


with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

setup(
    name="rhg_pulumi_resources",
    use_scm_version=True,
    description="Pulumi resource components and utilities for teaching and research at RHG",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/x-rst",
    author="Brewster Malevich",
    author_email="bmalevich@rhg.com",
    url="https://github.com/RhodiumGroup/rhg_pulumi_resourcesa",
    packages=find_packages(),
    python_requires=">=3.7",
    include_package_data=True,
    setup_requires=["setuptools_scm"],
    install_requires=[
        "pulumi>=2.0.0,<3.0.0",
        "pulumi-gcp>=3.19.0,<4.0.0",
        "pulumi-kubernetes>=1.0.0",
    ],
    zip_safe=False,
    keywords="pulumi",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
        "Topic :: System",
    ],
    extras_require={
        "test": ["pytest"],
        "dev": ["pytest", "pytest-cov", "wheel", "flake8", "pytest", "black", "twine"],
        "doc": ["sphinx", "sphinx_rtd_theme", "numpydoc", "ipython"],
    },
)

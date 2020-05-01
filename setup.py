import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nearup",  # Replace with your own username
    version="0.1.1",
    author="Near Inc",
    author_email="hello@near.org",
    description="Public scripts to launch near blockchain nodes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/near/nearup",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Clustering",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Networking"
    ],
    install_requires=[],
    python_requires='>=3.6',
    # scripts=['nearup'] # Intentionally no scripts, use as lib only if installed from pypi
)

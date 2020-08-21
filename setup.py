import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# ça marche point en faisant l'install :|

setuptools.setup(
    packages=setuptools.find_packages(),
    install_requires=["pykeepass>=3.2.0"],
    python_requires='>=3.6',
    name='connectionManagerPy',
    version='0.1',
    author="Alexandre Seris",
    description="Manage your various connections with python and get the corresponding standardised driver",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/boumabcd/connectionManager",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
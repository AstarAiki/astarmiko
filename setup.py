from setuptools import setup, find_packages

setup(
    name='astarmiko',
    version='0.1.0',
    description='Async SSH automation for enterprise network equipment',
    author='astaraiki',
    author_email='your.email@example.com',
    url='https://github.com/astaraiki/astarmiko',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'netmiko',
        'aiofiles',
        'asyncssh',
        'tqdm',
        'textfsm',
        'pyyaml',
        'requests',
        'pysnmp',
        'astarconf @ git+https://github.com/astaraiki/astarconf.git'
    ],
    entry_points={
        'console_scripts': [
            'astarmiko-cli=astarmiko.scripts.acm:main',
            'findhost=astarmiko.scripts.fh:main'
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)


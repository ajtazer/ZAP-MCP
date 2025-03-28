from setuptools import setup, find_packages

setup(
    name="mcp",
    version="1.6.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "websockets>=12.0",
    ],
    entry_points={
        'console_scripts': [
            'mcp-server=mcp.mcp_server:main',
        ],
    },
) 
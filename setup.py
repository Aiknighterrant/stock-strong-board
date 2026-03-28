#!/usr/bin/env python3
"""
沪深A股短线强势封板股分析技能安装脚本
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="stock-strong-board",
    version="1.0.0",
    author="Jackey",
    author_email="",
    description="沪深A股短线强势封板股分析技能",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Aiknighterrant/stock-strong-board",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "stock-strong-board=scripts.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt"],
    },
    keywords="stock, analysis, china, a股, 涨停, 封板, 短线, 投资",
    project_urls={
        "Bug Reports": "https://github.com/Aiknighterrant/stock-strong-board/issues",
        "Source": "https://github.com/Aiknighterrant/stock-strong-board",
    },
)
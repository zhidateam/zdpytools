from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="zdpytools",
    version="0.1.5",
    author="zhidateam",
    author_email="zhidateam@163.com",
    description="Python工具集，包含飞书API和日志工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zhidateam/zdpytools",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=[
        "loguru>=0.7.3",
        "httpx>=0.27.2",
        "pyyaml>=6.0.2",
        "oss2>=2.19.1"
    ],
)
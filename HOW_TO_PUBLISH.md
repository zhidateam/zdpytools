# 如何发布包到PyPI

本文档提供了将zdpytools包发布到PyPI的详细步骤。

## 准备工作

1. 确保已安装必要的打包工具：

```bash
pip install build twine
```

2. 确保你有PyPI账号，如果没有请在[PyPI官网](https://pypi.org/account/register/)注册。

## 打包流程

1. 清理之前的构建文件（如果有）：

```bash
rm -rf build/ dist/ *.egg-info/
# 或在Windows上 Powershell
Remove-Item -Recurse -Force build, dist, *.egg-info
```

2. 构建包：

```bash
python -m build
```

这将在`dist`目录下创建源代码分发包(`.tar.gz`)和轮子文件(`.whl`)。

3. 检查包是否正确：

```bash
twine check dist/*
```

## 测试发布

建议先发布到TestPyPI进行测试：

```bash
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

然后可以通过以下命令安装测试版本：

```bash
pip install --index-url https://test.pypi.org/simple/ zdpytools
```

## 正式发布

确认测试无误后，可以发布到正式PyPI：

```bash
twine upload dist/*
```

## 验证安装

发布完成后，验证包是否可以正常安装：

```bash
pip install zdpytools
```

## 版本更新

当需要更新包时，请修改以下文件中的版本号：

1. `zdpytools/__init__.py`中的`__version__`
2. `setup.py`中的`version`参数

然后重复上述打包和发布步骤。
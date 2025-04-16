#!/usr/bin/env python3
"""
打包脚本，用于构建zdpytools包并准备上传到PyPI
"""

import os
import sys
import shutil
import subprocess
import platform
import re

def clean_previous_builds():
    """清理之前的构建文件"""
    print("清理之前的构建文件...")
    dirs_to_clean = ["build", "dist", "zdpytools.egg-info"]

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"删除目录: {dir_name}")
            shutil.rmtree(dir_name)

def build_package():
    """构建包"""
    print("开始构建包...")
    result = subprocess.run([sys.executable, "-m", "build"], check=True)

    if result.returncode != 0:
        print("构建失败！")
        sys.exit(1)
    else:
        print("构建成功！")

def check_package():
    """检查包是否正确"""
    print("检查包是否正确...")
    if not os.path.exists("dist"):
        print("dist目录不存在，构建可能失败")
        sys.exit(1)

    dist_files = os.listdir("dist")
    if not dist_files:
        print("dist目录为空，构建可能失败")
        sys.exit(1)

    print("包文件:")
    for file in dist_files:
        print(f" - {file}")

    # 检查twine是否安装
    try:
        check_result = subprocess.run(["twine", "check", "dist/*"], shell=True, check=False)
        if check_result.returncode != 0:
            print("警告：包验证失败，请安装twine并手动检查")
    except Exception as e:
        print(f"无法验证包：{e}")
        print("请安装twine并运行: twine check dist/*")

def install_requirements():
    """安装构建所需依赖"""
    print("安装构建所需依赖...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "build", "twine"], check=True)
    except subprocess.CalledProcessError:
        print("安装依赖失败！")
        sys.exit(1)

def update_version():
    """自动更新版本号，将版本号末尾+0.01"""
    print("正在更新版本号...")

    # 更新 setup.py 中的版本号
    setup_path = "setup.py"
    with open(setup_path, "r", encoding="utf-8") as f:
        setup_content = f.read()

    # 使用正则表达式查找版本号
    setup_version_match = re.search(r'version="(\d+\.\d+\.\d+)"', setup_content)
    if not setup_version_match:
        print("无法在 setup.py 中找到版本号")
        return False

    current_version = setup_version_match.group(1)
    print(f"当前版本: {current_version}")

    # 解析版本号并增加0.01
    version_parts = current_version.split(".")
    if len(version_parts) != 3:
        print("版本号格式不正确，应为 x.y.z")
        return False

    major, minor, patch = version_parts
    new_patch = int(patch) + 1
    new_version = f"{major}.{minor}.{new_patch}"
    print(f"新版本: {new_version}")

    # 更新 setup.py
    new_setup_content = re.sub(
        r'version="(\d+\.\d+\.\d+)"',
        f'version="{new_version}"',
        setup_content
    )
    with open(setup_path, "w", encoding="utf-8") as f:
        f.write(new_setup_content)
    print(f"已更新 {setup_path} 中的版本号")

    # 更新 __init__.py 中的版本号
    init_path = "zdpytools/__init__.py"
    with open(init_path, "r", encoding="utf-8") as f:
        init_content = f.read()

    # 使用正则表达式查找版本号
    init_version_match = re.search(r'__version__ = "(\d+\.\d+\.\d+)"', init_content)
    if not init_version_match:
        print("无法在 __init__.py 中找到版本号")
        return False

    # 更新 __init__.py
    new_init_content = re.sub(
        r'__version__ = "(\d+\.\d+\.\d+)"',
        f'__version__ = "{new_version}"',
        init_content
    )
    with open(init_path, "w", encoding="utf-8") as f:
        f.write(new_init_content)
    print(f"已更新 {init_path} 中的版本号")

    return new_version

def read_api_key():
    """从 localtest/api.txt 读取 PyPI API 密钥"""
    api_key_path = "localtest/api.txt"
    if not os.path.exists(api_key_path):
        print(f"错误: {api_key_path} 不存在")
        return None

    try:
        with open(api_key_path, "r", encoding="utf-8") as f:
            api_key = f.read().strip()
        return api_key
    except Exception as e:
        print(f"读取 API 密钥失败: {e}")
        return None

def upload_to_pypi(api_key):
    """上传包到 PyPI"""
    print("正在上传到 PyPI...")

    # 设置环境变量
    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = api_key

    try:
        result = subprocess.run(
            ["twine", "upload", "dist/*"],
            env=env,
            check=True
        )
        if result.returncode == 0:
            print("上传成功！")
            return True
        else:
            print("上传失败！")
            return False
    except subprocess.CalledProcessError as e:
        print(f"上传失败: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("zdpytools 包构建工具")
    print("=" * 50)

    # 更新版本号
    new_version = update_version()
    if not new_version:
        print("版本更新失败，使用当前版本继续")

    # 安装依赖
    install_requirements()

    # 清理之前的构建
    clean_previous_builds()

    # 构建包
    build_package()

    # 检查包
    check_package()

    print("\n构建完成！")

    # 询问是否上传到 PyPI
    upload_choice = input("\n是否上传到 PyPI? (y/n): ").strip().lower()
    if upload_choice == 'y':
        api_key = read_api_key()
        if api_key:
            upload_to_pypi(api_key)
        else:
            print("无法获取 API 密钥，上传取消")
    else:
        print("已取消上传")
        print("要手动发布到TestPyPI，请运行:")
        print("twine upload --repository-url https://test.pypi.org/legacy/ dist/*")
        print("\n要手动发布到正式PyPI，请运行:")
        print("twine upload dist/*")

if __name__ == "__main__":
    main()
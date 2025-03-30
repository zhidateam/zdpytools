#!/usr/bin/env python3
"""
打包脚本，用于构建zdpytools包并准备上传到PyPI
"""

import os
import sys
import shutil
import subprocess
import platform

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

def main():
    """主函数"""
    print("=" * 50)
    print("zdpytools 包构建工具")
    print("=" * 50)

    # 安装依赖
    install_requirements()

    # 清理之前的构建
    clean_previous_builds()

    # 构建包
    build_package()

    # 检查包
    check_package()

    print("\n构建完成！")
    print("要发布到TestPyPI，请运行:")
    print("twine upload --repository-url https://test.pypi.org/legacy/ dist/*")
    print("\n要发布到正式PyPI，请运行:")
    print("twine upload dist/*")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双人抽奖 App - 一键 APK 打包脚本
使用 Buildozer 将 Python Kivy 应用打包为 Android APK

使用方法：
    python build.py

前提条件：
    - Python 3.7+
    - 网络连接（首次构建需要下载 Android SDK/NDK）

首次构建约需 15-30 分钟（需要下载大量依赖）
后续构建约需 5-10 分钟
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_banner(text):
    """打印横幅"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)


def run_cmd(cmd, cwd=None, check=True):
    """执行命令"""
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=False)
    if check and result.returncode != 0:
        print(f"\n✗ 命令执行失败，退出码: {result.returncode}")
        return False
    return True


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"✗ 需要 Python 3.7+，当前版本: {version.major}.{version.minor}")
        return False
    print(f"✓ Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True


def check_java():
    """检查 Java 环境"""
    result = subprocess.run("java -version", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("\n✗ 未检测到 Java")
        print("\n请安装 JDK 11 或更高版本:")
        print("  Windows: https://adoptium.net/")
        print("  Mac: brew install openjdk@17")
        print("  Linux: sudo apt install openjdk-17-jdk")
        print("\n安装后确保 java 命令可用")
        return False
    
    # 提取版本信息
    version_output = result.stderr or result.stdout
    print(f"✓ Java 已安装")
    print(f"  {version_output.split(chr(10))[0]}")
    return True


def install_dependencies():
    """安装依赖"""
    print_banner("安装依赖")
    
    # 升级 pip
    print("升级 pip...")
    if not run_cmd(f"{sys.executable} -m pip install --upgrade pip"):
        print("⚠️ pip 升级失败，继续尝试...")
    
    # 安装 buildozer
    print("\n安装 buildozer...")
    if not run_cmd(f"{sys.executable} -m pip install buildozer"):
        print("✗ 安装 buildozer 失败")
        return False
    print("✓ buildozer 已安装")
    
    # 安装 cython（buildozer 需要）
    print("\n安装 cython...")
    if not run_cmd(f"{sys.executable} -m pip install cython"):
        print("⚠️ cython 安装失败，可能影响构建")
    
    return True


def install_linux_dependencies():
    """安装 Linux 系统依赖（仅 Linux）"""
    if sys.platform != 'linux':
        return True
    
    print("\n检测 Linux 系统依赖...")
    
    # 检查必要的包
    packages = {
        'autoconf': 'autoconf',
        'automake': 'automake',
        'libtool': 'libtool',
        'pkg-config': 'pkg-config',
        'cmake': 'cmake',
        'gcc': 'build-essential',
        'zip': 'zip',
        'unzip': 'unzip'
    }
    
    missing = []
    for cmd, package in packages.items():
        result = subprocess.run(f"which {cmd}", shell=True, capture_output=True)
        if result.returncode != 0:
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ 缺少系统依赖: {', '.join(missing)}")
        print("\n请执行以下命令安装:")
        
        # 检测发行版
        if os.path.exists('/etc/debian_version'):
            print(f"  sudo apt update && sudo apt install -y {' '.join(missing)}")
        elif os.path.exists('/etc/redhat-release'):
            print(f"  sudo yum install -y {' '.join(missing)}")
        elif os.path.exists('/etc/arch-release'):
            print(f"  sudo pacman -S --noconfirm {' '.join(missing)}")
        else:
            print("  请手动安装以上依赖")
        
        print("\n安装完成后重新运行此脚本")
        return False
    
    print("✓ 所有系统依赖已满足")
    return True


def build_apk():
    """构建 APK"""
    print_banner("开始构建 APK")
    
    print("\n⚠️  重要提示:")
    print("  - 首次构建需要下载 Android SDK/NDK，约 2-3 GB")
    print("  - 请确保网络连接稳定")
    print("  - 构建过程约 15-30 分钟")
    print("  - 请勿中断构建过程\n")
    
    input("按 Enter 开始构建...")
    
    # 执行构建
    print("\n开始构建...")
    
    # 使用 buildozer 构建 debug APK
    cmd = f"{sys.executable} -m buildozer android debug"
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print("\n✗ 构建失败")
        print("\n常见错误及解决方案:")
        print("  1. Java 版本不匹配: 请安装 JDK 11 或 17")
        print("  2. 网络连接失败: 检查网络或使用代理")
        print("  3. 内存不足: 关闭其他程序后重试")
        print("  4. 磁盘空间不足: 确保有 10GB+ 可用空间")
        print("\n详细错误信息请查看 .buildozer/android/platform/build-*/logs/ 目录")
        return None
    
    # 查找生成的 APK
    print("\n✓ 构建完成！")
    
    apk_dir = Path("bin")
    if not apk_dir.exists():
        print("✗ 未找到 bin 目录")
        return None
    
    # 查找 APK 文件
    apks = list(apk_dir.glob("*.apk"))
    if not apks:
        print("✗ 未找到 APK 文件")
        return None
    
    apk_path = apks[0]
    print(f"\n🎉 APK 生成成功!")
    print(f"   文件: {apk_path}")
    print(f"   大小: {apk_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    return apk_path


def show_next_steps(apk_path):
    """显示后续步骤"""
    print_banner("构建完成！")
    
    print(f"\n✅ APK 文件位置:")
    print(f"   {apk_path.absolute()}")
    
    print(f"\n📱 安装到手机:")
    print(f"   1. 将 APK 文件传输到手机（USB/蓝牙/网盘）")
    print(f"   2. 在手机设置中开启「允许安装未知来源应用」")
    print(f"   3. 点击 APK 文件安装")
    
    print(f"\n🔧 常用命令:")
    print(f"   重新构建:        python -m buildozer android debug")
    print(f"   清理缓存:        python -m buildozer clean")
    print(f"   完全重置:        python -m buildozer distclean")
    print(f"   构建 release 版: python -m buildozer android release")
    
    print(f"\n💡 提示:")
    print(f"   - 如需修改应用，编辑 main.py 后重新构建")
    print(f"   - 修改 buildozer.spec 可调整应用配置")
    print(f"   - 详细文档: https://buildozer.readthedocs.io/")


def main():
    """主函数"""
    print_banner("双人抽奖 App APK 打包工具")
    print("\n本工具将帮你:")
    print("  1. 检查环境依赖")
    print("  2. 安装 Buildozer")
    print("  3. 构建 Android APK")
    print("\n首次构建约需 15-30 分钟，请耐心等待")
    
    # 检查 Python
    print_banner("步骤 1/4: 检查环境")
    if not check_python_version():
        sys.exit(1)
    
    # 检查 Java
    if not check_java():
        sys.exit(1)
    
    # 安装依赖
    print_banner("步骤 2/4: 安装依赖")
    if not install_dependencies():
        sys.exit(1)
    
    # Linux 系统依赖
    if not install_linux_dependencies():
        sys.exit(1)
    
    # 构建 APK
    print_banner("步骤 3/4: 构建 APK")
    apk_path = build_apk()
    if not apk_path:
        sys.exit(1)
    
    # 显示后续步骤
    show_next_steps(apk_path)
    
    print("\n" + "="*60)
    print("  全部完成！享受你的双人抽奖 App 吧！ 🎰")
    print("="*60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消构建")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

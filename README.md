# 双人抽奖 App - Python Kivy 版本

纯 Python 实现的双人抽奖应用，使用 Kivy 框架开发，支持一键打包为 Android APK。

## 🎮 功能特性

- **奖池管理**：创建、编辑、删除奖池，自定义奖项（支持 emoji）
- **双人触控抽奖**：两人同时按住屏幕，倒计时后老虎机滚动，松手定格结果
- **抽奖历史**：记录每次抽奖结果，支持删除和清空
- **设置**：音效/振动开关、数据导入导出、重置数据
- **本地存储**：所有数据保存在本地，无需网络

## 📦 快速开始

### 方法一：一键打包（推荐）

```bash
# 1. 确保已安装 Python 3.7+ 和 Java 11+

# 2. 运行打包脚本
python build.py

# 3. 等待构建完成（首次约 15-30 分钟）
# 4. APK 文件生成在 bin/ 目录
```

### 方法二：手动打包

```bash
# 1. 安装 buildozer
pip install buildozer cython

# 2. 构建 APK
buildozer android debug

# 3. APK 在 bin/ 目录
```

### 方法三：本地运行测试（不生成 APK）

```bash
# 1. 安装 kivy
pip install kivy

# 2. 运行应用
python main.py
```

## 📁 项目结构

```
lottery_kivy/
├── main.py           # 主应用代码
├── buildozer.spec    # APK 打包配置
├── build.py          # 一键打包脚本
└── README.md         # 本文件
```

## ⚙️ 系统要求

### 打包 APK
- **Python**: 3.7+
- **Java**: JDK 11 或 17（推荐 [Adoptium](https://adoptium.net/)）
- **磁盘空间**: 10GB+（首次构建需要下载 Android SDK/NDK）
- **网络**: 稳定的网络连接

### Linux 额外依赖
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y autoconf automake libtool pkg-config cmake build-essential gcc zip unzip

# Arch Linux
sudo pacman -S base-devel cmake zip unzip
```

### macOS
```bash
# 使用 Homebrew
brew install autoconf automake libtool pkg-config cmake
```

### Windows
Windows 用户建议使用 [WSL2](https://docs.microsoft.com/windows/wsl/) 进行打包。

## 🎯 使用指南

### 创建奖池
1. 打开应用，点击「+ 创建奖池」
2. 输入奖池名称（如"今晚吃什么"）
3. 输入奖项列表（每行一个，或用逗号分隔）
4. 点击保存

### 双人抽奖
1. 点击奖池卡片上的「🎲 开始抽奖」
2. 两人分别按住屏幕上下区域
3. 等待 3 秒倒计时
4. 奖项开始滚动
5. 任意一方松手，结果定格

### 数据管理
- **导出**：设置 → 导出数据 → 生成 JSON 备份文件
- **导入**：将备份文件命名为 `import.json` 放在应用目录 → 设置 → 导入数据
- **重置**：设置 → 重置所有数据（不可恢复！）

## 🔧 自定义配置

编辑 `buildozer.spec` 可修改：
- `title`：应用名称
- `package.name`：包名
- `version`：版本号
- `orientation`：屏幕方向

## 🐛 常见问题

### 构建失败：Java 版本不匹配
```
请安装 JDK 11 或 17，确保 java -version 显示正确版本
```

### 构建失败：网络问题
```
检查网络连接，或使用代理：
export https_proxy=http://your-proxy:port
```

### 构建失败：内存不足
```
关闭其他程序，确保有 4GB+ 可用内存
```

### APK 安装失败
```
1. 确保手机已开启「允许安装未知来源应用」
2. 检查手机存储空间
3. 尝试删除旧版本后重新安装
```

### 多点触控不灵敏
```
这是 Kivy 的已知限制，在桌面模拟器上可能表现不佳
真机上体验更佳
```

## 📚 技术栈

- **Python 3.7+**：主要开发语言
- **Kivy**：跨平台 UI 框架
- **Buildozer**：APK 打包工具
- **JsonStore**：本地数据存储

## 📄 许可证

MIT License - 自由使用和修改

## 🎉 开始使用

```bash
python build.py
```

享受你的双人抽奖 App 吧！🎰

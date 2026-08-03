[app]

# (str) 应用标题
title = 双人抽奖

# (str) 包名
package.name = lotteryapp

# (str) 包域名
package.domain = org.example.lottery

# (str) 源码目录
source.dir = .

# (list) 包含的文件
source.include_exts = .py,.png,.jpg,.kv,.atlas,.json,.ttf,.mp3

# (str) 应用版本号
version = 1.0.0

# (list) 依赖库
# 核心依赖：kivy 框架
requirements = python3,kivy

# (str) _orientation 屏幕方向: portrait, landscape, sensor
orientation = portrait

# (bool) 是否全屏
fullscreen = 0

# (list) Android 权限
android.permissions = VIBRATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) 最低 API 版本
android.minapi = 21

# (int) 目标 API 版本
android.api = 33

# (str) Android NDK 版本
android.ndk = 25b
android.accept_sdk_license = True
# (bool) 是否允许备份
android.allow_backup = True

# (str) 日志等级
log_level = 2

# (str) Buildozer 警告等级
warn_on_root = 1

# (str) 日志路径
# log_path = .buildozer/log

# ================================================================================
# 开发者模式（仅开发时使用）
# ================================================================================

[buildozer]

# (int) 日志等级
log_level = 2

# (int) 显示警告
warn_on_root = 1

# (str) Buildozer 路径
# buildozer_dir = .buildozer

# ================================================================================
# 安卓特定配置
# ================================================================================

[app:source.include_patterns]
# 包含的数据文件
assets/*,data/*.json

[app:android]
# Android 特定配置
# 图标和启动画面（可选）
# icon.filename = assets/icon.png
# presplash.filename = assets/presplash.png

# 权限
permissions = VIBRATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# 特性
android.features = android.hardware.touchscreen.multitouch
p4a.url = https://ghfast.top/https://github.com/kivy/python-for-android.git

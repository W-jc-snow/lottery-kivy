# -*- coding: utf-8 -*-
"""
双人抽奖 App - Python Kivy 版本
支持 Android/iOS 打包，无需 Expo

功能：
- 奖池管理（创建/编辑/删除）
- 双人触控抽奖
- 抽奖历史
- 设置（音效/振动/数据管理）
"""

import json
import os
import random
import time
import uuid
from datetime import datetime
from pathlib import Path

# ==================== 中文字体配置 ====================
import platform

def get_chinese_font():
    """根据操作系统获取中文字体路径"""
    system = platform.system()
    
    if system == 'Windows':
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/simsun.ttc',
        ]
    elif system == 'Darwin':
        font_paths = [
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/PingFang.ttc',
        ]
    else:
        font_paths = [
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',
        ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path
    return None

chinese_font = get_chinese_font()

# 写入 kivy 配置文件
if chinese_font:
    kivy_dir = os.path.join(os.path.expanduser('~'), '.kivy')
    os.makedirs(kivy_dir, exist_ok=True)
    config_path = os.path.join(kivy_dir, 'config.ini')
    
    # 直接写入配置文件
    font_line = f"default_font = ['chinese', '{chinese_font}', '{chinese_font}', '{chinese_font}', '{chinese_font}']"
    
    lines = ['[kivy]\n', font_line + '\n']
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            existing = f.read()
        # 如果已有 [kivy] 段，替换 default_font 行
        if '[kivy]' in existing:
            import re
            existing = re.sub(r'default_font\s*=.*', font_line, existing)
            lines = [existing]
        else:
            lines = [existing.rstrip() + '\n\n'] + lines
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    from kivy.core.text import LabelBase
    LabelBase.register(name='chinese', fn_regular=chinese_font)
    print(f"已配置中文字体: {chinese_font}")
    print(f"配置文件: {config_path}")
else:
    print("警告: 未找到中文字体")

import kivy
kivy.require('2.0.0')

# ==================== Kivy 导入 ====================
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
from kivy.properties import (BooleanProperty, ListProperty, NumericProperty,
                             StringProperty)
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.metrics import dp

# 尝试导入振动模块（仅 Android 可用）
try:
    from android import api_version
    import android
    CAN_VIBRATE = True
except ImportError:
    CAN_VIBRATE = False

# ==================== 数据文件路径 ====================
DATA_DIR = Path(__file__).parent
POOLS_FILE = DATA_DIR / "pools.json"
HISTORY_FILE = DATA_DIR / "history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"


# ==================== 数据管理 ====================

class DataManager:
    """数据管理器 - 处理所有持久化存储"""
    
    def __init__(self):
        self.pools = []
        self.history = []
        self.settings = {
            "sound_enabled": True,
            "vibration_enabled": True,
            "animation_theme": "classic"
        }
        self.load_all()
    
    def load_all(self):
        """加载所有数据"""
        self.pools = self._load_json(POOLS_FILE, [])
        self.history = self._load_json(HISTORY_FILE, [])
        self.settings = self._load_json(SETTINGS_FILE, self.settings)
    
    def _load_json(self, filepath, default):
        """从 JSON 文件加载数据"""
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载 {filepath} 失败: {e}")
        return default
    
    def _save_json(self, filepath, data):
        """保存数据到 JSON 文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存 {filepath} 失败: {e}")
            return False
    
    # 奖池操作
    def add_pool(self, name, items):
        """创建奖池"""
        pool = {
            "id": str(uuid.uuid4()),
            "name": name,
            "items": items,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_draw": None
        }
        self.pools.append(pool)
        self._save_json(POOLS_FILE, self.pools)
        return pool
    
    def update_pool(self, pool_id, name=None, items=None):
        """更新奖池"""
        for pool in self.pools:
            if pool["id"] == pool_id:
                if name:
                    pool["name"] = name
                if items:
                    pool["items"] = items
                pool["updated_at"] = datetime.now().isoformat()
                self._save_json(POOLS_FILE, self.pools)
                return True
        return False
    
    def delete_pool(self, pool_id):
        """删除奖池"""
        self.pools = [p for p in self.pools if p["id"] != pool_id]
        self._save_json(POOLS_FILE, self.pools)
    
    def get_pool(self, pool_id):
        """获取奖池"""
        for pool in self.pools:
            if pool["id"] == pool_id:
                return pool
        return None
    
    def update_pool_last_draw(self, pool_id):
        """更新奖池最后抽奖时间"""
        for pool in self.pools:
            if pool["id"] == pool_id:
                pool["last_draw"] = datetime.now().isoformat()
                self._save_json(POOLS_FILE, self.pools)
                break
    
    # 历史记录操作
    def add_history(self, pool_name, result, mode="单机双人"):
        """添加抽奖历史"""
        record = {
            "id": str(uuid.uuid4()),
            "pool_name": pool_name,
            "result": result,
            "mode": mode,
            "timestamp": datetime.now().isoformat()
        }
        self.history.insert(0, record)  # 最新的在前面
        self._save_json(HISTORY_FILE, self.history)
        return record
    
    def delete_history(self, record_id):
        """删除单条历史"""
        self.history = [h for h in self.history if h["id"] != record_id]
        self._save_json(HISTORY_FILE, self.history)
    
    def clear_history(self):
        """清空所有历史"""
        self.history = []
        self._save_json(HISTORY_FILE, self.history)
    
    # 设置操作
    def get_setting(self, key, default=None):
        """获取设置"""
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """设置值"""
        self.settings[key] = value
        self._save_json(SETTINGS_FILE, self.settings)
    
    # 数据导入导出
    def export_data(self):
        """导出所有数据为 JSON"""
        return {
            "pools": self.pools,
            "history": self.history,
            "settings": self.settings,
            "exported_at": datetime.now().isoformat()
        }
    
    def import_data(self, data):
        """导入数据"""
        if "pools" in data:
            self.pools = data["pools"]
            self._save_json(POOLS_FILE, self.pools)
        if "history" in data:
            self.history = data["history"]
            self._save_json(HISTORY_FILE, self.history)
        if "settings" in data:
            self.settings = data["settings"]
            self._save_json(SETTINGS_FILE, self.settings)
    
    def reset_all(self):
        """重置所有数据"""
        self.pools = []
        self.history = []
        self.settings = {
            "sound_enabled": True,
            "vibration_enabled": True,
            "animation_theme": "classic"
        }
        self._save_json(POOLS_FILE, self.pools)
        self._save_json(HISTORY_FILE, self.history)
        self._save_json(SETTINGS_FILE, self.settings)


# 全局数据管理器
data_manager = DataManager()


# ==================== UI 组件 ====================

class CardButton(Button):
    """卡片样式按钮"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = dp(16)
        self.size_hint_y = None
        self.height = dp(80)


class PoolCard(BoxLayout):
    """奖池卡片组件"""
    
    def __init__(self, pool, **kwargs):
        super().__init__(**kwargs)
        self.pool = pool
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(100)
        self.padding = dp(10)
        self.spacing = dp(5)
        
        # 背景
        with self.canvas.before:
            self.bg_color = Color(0.2, 0.2, 0.25, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # 奖池名称
        name_label = Label(
            text=pool["name"],
            font_size=dp(18),
            bold=True,
            size_hint_y=0.4,
            halign='left',
            valign='middle'
        )
        name_label.bind(size=name_label.setter('text_size'))
        self.add_widget(name_label)
        
        # 奖项数量
        items_count = len(pool.get("items", []))
        info_text = f"奖项数: {items_count}"
        if pool.get("last_draw"):
            try:
                dt = datetime.fromisoformat(pool["last_draw"])
                info_text += f"  |  上次抽奖: {dt.strftime('%m-%d %H:%M')}"
            except:
                pass
        
        info_label = Label(
            text=info_text,
            font_size=dp(13),
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=0.3,
            halign='left',
            valign='middle'
        )
        info_label.bind(size=info_label.setter('text_size'))
        self.add_widget(info_label)
    
    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


# ==================== 页面 ====================

class PoolListScreen(Screen):
    """奖池列表页面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'pool_list'
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # 标题
        title = Label(
            text='🎰 双人抽奖',
            font_size=dp(24),
            bold=True,
            size_hint_y=0.1,
            color=(1, 0.7, 0.3, 1)
        )
        layout.add_widget(title)
        
        # 奖池列表（滚动）
        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.pool_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        self.pool_list.bind(minimum_height=self.pool_list.setter('height'))
        self.scroll.add_widget(self.pool_list)
        layout.add_widget(self.scroll)
        
        # 底部按钮
        btn_layout = BoxLayout(size_hint_y=0.1, spacing=dp(10))
        
        # 历史记录按钮
        history_btn = Button(
            text='📋 历史',
            font_size=dp(14),
            background_color=(0.3, 0.3, 0.35, 1),
            color=(1, 1, 1, 1)
        )
        history_btn.bind(on_press=self.go_to_history)
        btn_layout.add_widget(history_btn)
        
        # 设置按钮
        settings_btn = Button(
            text='⚙️ 设置',
            font_size=dp(14),
            background_color=(0.3, 0.3, 0.35, 1),
            color=(1, 1, 1, 1)
        )
        settings_btn.bind(on_press=self.go_to_settings)
        btn_layout.add_widget(settings_btn)
        
        # 创建奖池按钮
        create_btn = Button(
            text='+ 创建奖池',
            font_size=dp(14),
            background_color=(1, 0.6, 0.2, 1),
            color=(1, 1, 1, 1),
            bold=True
        )
        create_btn.bind(on_press=self.create_pool)
        btn_layout.add_widget(create_btn)
        
        layout.add_widget(btn_layout)
        self.add_widget(layout)
    
    def on_enter(self):
        """进入页面时刷新列表"""
        self.refresh_pools()
    
    def refresh_pools(self):
        """刷新奖池列表"""
        self.pool_list.clear_widgets()
        
        if not data_manager.pools:
            empty_label = Label(
                text='暂无奖池\n点击「+ 创建奖池」开始',
                font_size=dp(16),
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=dp(150)
            )
            self.pool_list.add_widget(empty_label)
            return
        
        for pool in data_manager.pools:
            card = PoolCard(pool)
            
            # 按钮区域
            btn_box = BoxLayout(size_hint_y=0.3, spacing=dp(5))
            
            # 编辑按钮
            edit_btn = Button(
                text='编辑',
                font_size=dp(12),
                size_hint_x=0.3,
                background_color=(0.3, 0.5, 0.8, 1)
            )
            edit_btn.bind(on_press=lambda x, p=pool: self.edit_pool(p))
            btn_box.add_widget(edit_btn)
            
            # 开始抽奖按钮
            draw_btn = Button(
                text='🎲 开始抽奖',
                font_size=dp(12),
                size_hint_x=0.5,
                background_color=(1, 0.5, 0.2, 1),
                bold=True
            )
            draw_btn.bind(on_press=lambda x, p=pool: self.start_draw(p))
            btn_box.add_widget(draw_btn)
            
            # 删除按钮
            del_btn = Button(
                text='删除',
                font_size=dp(12),
                size_hint_x=0.2,
                background_color=(0.8, 0.2, 0.2, 1)
            )
            del_btn.bind(on_press=lambda x, p=pool: self.confirm_delete_pool(p))
            btn_box.add_widget(del_btn)
            
            card.add_widget(btn_box)
            self.pool_list.add_widget(card)
    
    def create_pool(self, instance):
        """创建奖池弹窗"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        name_input = TextInput(
            hint_text='奖池名称（必填）',
            multiline=False,
            font_size=dp(16),
            size_hint_y=0.2
        )
        content.add_widget(name_input)
        
        items_input = TextInput(
            hint_text='奖项列表（每行一个，或用逗号分隔）\n例如：\n火锅 🍲\n日料 🍣\n麻辣烫',
            multiline=True,
            font_size=dp(14),
            size_hint_y=0.6
        )
        content.add_widget(items_input)
        
        btn_box = BoxLayout(size_hint_y=0.2, spacing=dp(10))
        
        def save_pool(instance):
            name = name_input.text.strip()
            if not name:
                self.show_error("请输入奖池名称")
                return
            
            # 解析奖项
            items_text = items_input.text.strip()
            if not items_text:
                self.show_error("请至少输入一个奖项")
                return
            
            # 支持换行或逗号分隔
            items = [item.strip() for item in items_text.replace(',', '\n').split('\n') if item.strip()]
            
            if len(items) < 2:
                self.show_error("至少需要2个奖项")
                return
            
            data_manager.add_pool(name, items)
            popup.dismiss()
            self.refresh_pools()
        
        def cancel(instance):
            popup.dismiss()
        
        save_btn = Button(text='保存', background_color=(0.2, 0.7, 0.3, 1))
        save_btn.bind(on_press=save_pool)
        btn_box.add_widget(save_btn)
        
        cancel_btn = Button(text='取消', background_color=(0.5, 0.5, 0.5, 1))
        cancel_btn.bind(on_press=cancel)
        btn_box.add_widget(cancel_btn)
        
        content.add_widget(btn_box)
        
        popup = Popup(
            title='创建奖池',
            content=content,
            size_hint=(0.9, 0.7),
            auto_dismiss=False
        )
        popup.open()
    
    def edit_pool(self, pool):
        """编辑奖池"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        name_input = TextInput(
            text=pool["name"],
            multiline=False,
            font_size=dp(16),
            size_hint_y=0.2
        )
        content.add_widget(name_input)
        
        items_text = '\n'.join(pool.get("items", []))
        items_input = TextInput(
            text=items_text,
            multiline=True,
            font_size=dp(14),
            size_hint_y=0.6
        )
        content.add_widget(items_input)
        
        btn_box = BoxLayout(size_hint_y=0.2, spacing=dp(10))
        
        def save_pool(instance):
            name = name_input.text.strip()
            if not name:
                self.show_error("请输入奖池名称")
                return
            
            items = [item.strip() for item in items_input.text.replace(',', '\n').split('\n') if item.strip()]
            
            if len(items) < 2:
                self.show_error("至少需要2个奖项")
                return
            
            data_manager.update_pool(pool["id"], name=name, items=items)
            popup.dismiss()
            self.refresh_pools()
        
        def cancel(instance):
            popup.dismiss()
        
        save_btn = Button(text='保存', background_color=(0.2, 0.7, 0.3, 1))
        save_btn.bind(on_press=save_pool)
        btn_box.add_widget(save_btn)
        
        cancel_btn = Button(text='取消', background_color=(0.5, 0.5, 0.5, 1))
        cancel_btn.bind(on_press=cancel)
        btn_box.add_widget(cancel_btn)
        
        content.add_widget(btn_box)
        
        popup = Popup(
            title='编辑奖池',
            content=content,
            size_hint=(0.9, 0.7),
            auto_dismiss=False
        )
        popup.open()
    
    def confirm_delete_pool(self, pool):
        """确认删除奖池"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        label = Label(
            text=f'确定要删除奖池「{pool["name"]}」吗？\n此操作不可恢复',
            font_size=dp(16)
        )
        content.add_widget(label)
        
        btn_box = BoxLayout(size_hint_y=0.3, spacing=dp(10))
        
        def confirm(instance):
            data_manager.delete_pool(pool["id"])
            popup.dismiss()
            self.refresh_pools()
        
        def cancel(instance):
            popup.dismiss()
        
        del_btn = Button(text='删除', background_color=(0.8, 0.2, 0.2, 1))
        del_btn.bind(on_press=confirm)
        btn_box.add_widget(del_btn)
        
        cancel_btn = Button(text='取消', background_color=(0.5, 0.5, 0.5, 1))
        cancel_btn.bind(on_press=cancel)
        btn_box.add_widget(cancel_btn)
        
        content.add_widget(btn_box)
        
        popup = Popup(
            title='确认删除',
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        popup.open()
    
    def start_draw(self, pool):
        """开始抽奖"""
        if len(pool.get("items", [])) < 2:
            self.show_error("奖池至少需要2个奖项")
            return
        
        # 传递奖池信息到抽奖页面
        draw_screen = self.manager.get_screen('draw')
        draw_screen.set_pool(pool)
        self.manager.current = 'draw'
    
    def go_to_history(self, instance):
        """跳转到历史记录"""
        self.manager.current = 'history'
    
    def go_to_settings(self, instance):
        """跳转到设置"""
        self.manager.current = 'settings'
    
    def show_error(self, message):
        """显示错误提示"""
        popup = Popup(
            title='错误',
            content=Label(text=message, font_size=dp(16)),
            size_hint=(0.7, 0.3)
        )
        popup.open()


class DrawScreen(Screen):
    """双人抽奖页面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'draw'
        
        self.pool = None
        self.is_rolling = False
        self.current_item = ""
        self.player1_pressed = False
        self.player2_pressed = False
        self.countdown = 0
        self.touch_ids = {}
        
        self.build_ui()
    
    def build_ui(self):
        """构建界面"""
        self.clear_widgets()
        
        # 主布局
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # 顶部信息栏
        top_bar = BoxLayout(size_hint_y=0.1, spacing=dp(10))
        
        self.pool_name_label = Label(
            text='奖池: ',
            font_size=dp(16),
            size_hint_x=0.7,
            halign='left',
            valign='middle'
        )
        self.pool_name_label.bind(size=self.pool_name_label.setter('text_size'))
        top_bar.add_widget(self.pool_name_label)
        
        back_btn = Button(
            text='← 返回',
            font_size=dp(14),
            size_hint_x=0.3,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        back_btn.bind(on_press=self.go_back)
        top_bar.add_widget(back_btn)
        
        layout.add_widget(top_bar)
        
        # 玩家1区域（上半部分）
        self.player1_area = BoxLayout(
            orientation='vertical',
            size_hint_y=0.35,
            padding=dp(20)
        )
        with self.player1_area.canvas.before:
            Color(0.2, 0.4, 0.7, 0.8)
            self.p1_bg = RoundedRectangle(pos=self.player1_area.pos, size=self.player1_area.size, radius=[dp(15)])
        self.player1_area.bind(pos=self._update_p1_bg, size=self._update_p1_bg)
        
        p1_label = Label(
            text='玩家1\n按住此处',
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 0.9)
        )
        self.player1_area.add_widget(p1_label)
        layout.add_widget(self.player1_area)
        
        # 中央显示区域
        self.center_area = BoxLayout(
            orientation='vertical',
            size_hint_y=0.25,
            padding=dp(10)
        )
        with self.center_area.canvas.before:
            Color(0.15, 0.15, 0.2, 1)
            self.center_bg = RoundedRectangle(pos=self.center_area.pos, size=self.center_area.size, radius=[dp(10)])
        self.center_area.bind(pos=self._update_center_bg, size=self._update_center_bg)
        
        self.center_label = Label(
            text='两人同时按住\n开始抽奖',
            font_size=dp(18),
            bold=True,
            color=(1, 0.8, 0.3, 1)
        )
        self.center_area.add_widget(self.center_label)
        layout.add_widget(self.center_area)
        
        # 玩家2区域（下半部分）
        self.player2_area = BoxLayout(
            orientation='vertical',
            size_hint_y=0.35,
            padding=dp(20)
        )
        with self.player2_area.canvas.before:
            Color(0.7, 0.3, 0.2, 0.8)
            self.p2_bg = RoundedRectangle(pos=self.player2_area.pos, size=self.player2_area.size, radius=[dp(15)])
        self.player2_area.bind(pos=self._update_p2_bg, size=self._update_p2_bg)
        
        p2_label = Label(
            text='玩家2\n按住此处',
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 0.9)
        )
        self.player2_area.add_widget(p2_label)
        layout.add_widget(self.player2_area)
        
        self.add_widget(layout)
    
    def _update_p1_bg(self, *args):
        self.p1_bg.pos = self.player1_area.pos
        self.p1_bg.size = self.player1_area.size
    
    def _update_p2_bg(self, *args):
        self.p2_bg.pos = self.player2_area.pos
        self.p2_bg.size = self.player2_area.size
    
    def _update_center_bg(self, *args):
        self.center_bg.pos = self.center_area.pos
        self.center_bg.size = self.center_area.size
    
    def set_pool(self, pool):
        """设置当前奖池"""
        self.pool = pool
        self.pool_name_label.text = f'奖池: {pool["name"]}'
        self.reset_game()
    
    def reset_game(self):
        """重置游戏状态"""
        self.is_rolling = False
        self.player1_pressed = False
        self.player2_pressed = False
        self.countdown = 0
        self.center_label.text = '两人同时按住\n开始抽奖'
        self.center_label.color = (1, 0.8, 0.3, 1)
    
    def on_touch_down(self, touch):
        """触摸开始"""
        if self.is_rolling:
            # 滚动中触摸 = 停止
            self.stop_rolling()
            return True
        
        # 判断触摸区域
        if self.player1_area.collide_point(*touch.pos):
            self.touch_ids['player1'] = touch.uid
            self.player1_pressed = True
            self.check_both_pressed()
            return True
        elif self.player2_area.collide_point(*touch.pos):
            self.touch_ids['player2'] = touch.uid
            self.player2_pressed = True
            self.check_both_pressed()
            return True
        
        return super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        """触摸结束"""
        if touch.uid == self.touch_ids.get('player1'):
            self.player1_pressed = False
            del self.touch_ids['player1']
            if self.countdown > 0:
                # 倒计时期间松手 = 重置
                self.reset_game()
                self.center_label.text = '两人需同时按住！'
            elif self.is_rolling:
                self.stop_rolling()
            return True
        elif touch.uid == self.touch_ids.get('player2'):
            self.player2_pressed = False
            del self.touch_ids['player2']
            if self.countdown > 0:
                self.reset_game()
                self.center_label.text = '两人需同时按住！'
            elif self.is_rolling:
                self.stop_rolling()
            return True
        
        return super().on_touch_up(touch)
    
    def check_both_pressed(self):
        """检查是否两人都按住了"""
        if self.player1_pressed and self.player2_pressed and not self.is_rolling:
            self.start_countdown()
    
    def start_countdown(self):
        """开始倒计时"""
        self.countdown = 3
        self.center_label.text = '3'
        self.center_label.font_size = dp(48)
        self.center_label.color = (1, 0.5, 0.2, 1)
        
        Clock.schedule_once(self.countdown_tick, 1)
    
    def countdown_tick(self, dt):
        """倒计时tick"""
        self.countdown -= 1
        
        if self.countdown > 0:
            self.center_label.text = str(self.countdown)
            Clock.schedule_once(self.countdown_tick, 1)
        else:
            # 倒计时结束，开始滚动
            self.center_label.font_size = dp(24)
            self.start_rolling()
    
    def start_rolling(self):
        """开始滚动奖项"""
        self.is_rolling = True
        items = self.pool.get("items", [])
        
        def roll_tick(dt):
            if not self.is_rolling:
                return False
            
            item = random.choice(items)
            self.center_label.text = item
            return True
        
        # 每 0.1 秒切换一次
        Clock.schedule_interval(roll_tick, 0.1)
    
    def stop_rolling(self):
        """停止滚动并显示结果"""
        self.is_rolling = False
        
        if not self.pool:
            return
        
        # 随机选择结果
        items = self.pool.get("items", [])
        result = random.choice(items)
        
        # 显示结果
        self.center_label.text = f'🎉 {result} 🎉'
        self.center_label.font_size = dp(32)
        self.center_label.color = (1, 0.9, 0.2, 1)
        self.center_label.bold = True
        
        # 振动反馈
        if data_manager.get_setting("vibration_enabled", True) and CAN_VIBRATE:
            try:
                android.vibrate(0.3)
            except:
                pass
        
        # 保存历史记录
        data_manager.add_history(self.pool["name"], result)
        data_manager.update_pool_last_draw(self.pool["id"])
        
        # 2秒后显示操作按钮
        Clock.schedule_once(self.show_result_buttons, 1.5)
    
    def show_result_buttons(self, dt):
        """显示结果页操作按钮"""
        btn_box = BoxLayout(size_hint_y=0.1, spacing=dp(10))
        
        again_btn = Button(
            text='🔄 再来一次',
            font_size=dp(14),
            background_color=(0.3, 0.6, 0.9, 1)
        )
        again_btn.bind(on_press=lambda x: self.reset_game())
        btn_box.add_widget(again_btn)
        
        back_btn = Button(
            text='← 返回奖池',
            font_size=dp(14),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        back_btn.bind(on_press=self.go_back)
        btn_box.add_widget(back_btn)
        
        # 检查是否已有按钮
        for child in self.children:
            if isinstance(child, BoxLayout):
                for sub_child in child.children:
                    if isinstance(sub_child, BoxLayout) and sub_child.size_hint_y == 0.1:
                        # 移除旧按钮
                        self.remove_widget(sub_child)
                        break
        
        self.add_widget(btn_box)
    
    def go_back(self, instance):
        """返回奖池列表"""
        self.reset_game()
        self.manager.current = 'pool_list'


class HistoryScreen(Screen):
    """历史记录页面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'history'
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # 标题栏
        top_bar = BoxLayout(size_hint_y=0.1, spacing=dp(10))
        
        back_btn = Button(
            text='← 返回',
            font_size=dp(14),
            size_hint_x=0.3,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        back_btn.bind(on_press=self.go_back)
        top_bar.add_widget(back_btn)
        
        title = Label(
            text='📋 抽奖历史',
            font_size=dp(20),
            bold=True,
            size_hint_x=0.5
        )
        top_bar.add_widget(title)
        
        clear_btn = Button(
            text='清空全部',
            font_size=dp(12),
            size_hint_x=0.2,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        clear_btn.bind(on_press=self.confirm_clear)
        top_bar.add_widget(clear_btn)
        
        layout.add_widget(top_bar)
        
        # 历史列表
        self.scroll = ScrollView(size_hint=(1, 0.9))
        self.history_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8))
        self.history_list.bind(minimum_height=self.history_list.setter('height'))
        self.scroll.add_widget(self.history_list)
        layout.add_widget(self.scroll)
        
        self.add_widget(layout)
    
    def on_enter(self):
        """进入页面时刷新"""
        self.refresh_history()
    
    def refresh_history(self):
        """刷新历史列表"""
        self.history_list.clear_widgets()
        
        if not data_manager.history:
            empty_label = Label(
                text='暂无抽奖记录',
                font_size=dp(16),
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=dp(100)
            )
            self.history_list.add_widget(empty_label)
            return
        
        for record in data_manager.history[:50]:  # 最多显示50条
            item = self.create_history_item(record)
            self.history_list.add_widget(item)
    
    def create_history_item(self, record):
        """创建历史记录项"""
        box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            padding=dp(8),
            spacing=dp(4)
        )
        
        with box.canvas.before:
            Color(0.2, 0.2, 0.25, 1)
            bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])
        box.bind(pos=lambda *args: setattr(bg, 'pos', box.pos),
                 size=lambda *args: setattr(bg, 'size', box.size))
        
        # 第一行：奖池名 + 结果
        top = BoxLayout(size_hint_y=0.5)
        
        pool_label = Label(
            text=f'🎰 {record["pool_name"]}',
            font_size=dp(14),
            bold=True,
            size_hint_x=0.5,
            halign='left',
            valign='middle'
        )
        pool_label.bind(size=pool_label.setter('text_size'))
        top.add_widget(pool_label)
        
        result_label = Label(
            text=f'🎁 {record["result"]}',
            font_size=dp(14),
            color=(1, 0.8, 0.3, 1),
            size_hint_x=0.5,
            halign='right',
            valign='middle'
        )
        result_label.bind(size=result_label.setter('text_size'))
        top.add_widget(result_label)
        
        box.add_widget(top)
        
        # 第二行：时间 + 删除按钮
        bottom = BoxLayout(size_hint_y=0.5)
        
        try:
            dt = datetime.fromisoformat(record["timestamp"])
            time_text = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            time_text = record.get("timestamp", "")
        
        time_label = Label(
            text=f'🕐 {time_text}',
            font_size=dp(12),
            color=(0.6, 0.6, 0.6, 1),
            size_hint_x=0.7,
            halign='left',
            valign='middle'
        )
        time_label.bind(size=time_label.setter('text_size'))
        bottom.add_widget(time_label)
        
        del_btn = Button(
            text='删除',
            font_size=dp(11),
            size_hint_x=0.3,
            background_color=(0.6, 0.2, 0.2, 1)
        )
        del_btn.bind(on_press=lambda x, r=record: self.delete_record(r))
        bottom.add_widget(del_btn)
        
        box.add_widget(bottom)
        
        return box
    
    def delete_record(self, record):
        """删除单条记录"""
        data_manager.delete_history(record["id"])
        self.refresh_history()
    
    def confirm_clear(self, instance):
        """确认清空所有记录"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        label = Label(
            text='确定要清空所有抽奖记录吗？\n此操作不可恢复',
            font_size=dp(16)
        )
        content.add_widget(label)
        
        btn_box = BoxLayout(size_hint_y=0.3, spacing=dp(10))
        
        def confirm(instance):
            data_manager.clear_history()
            popup.dismiss()
            self.refresh_history()
        
        def cancel(instance):
            popup.dismiss()
        
        clear_btn = Button(text='清空', background_color=(0.8, 0.2, 0.2, 1))
        clear_btn.bind(on_press=confirm)
        btn_box.add_widget(clear_btn)
        
        cancel_btn = Button(text='取消', background_color=(0.5, 0.5, 0.5, 1))
        cancel_btn.bind(on_press=cancel)
        btn_box.add_widget(cancel_btn)
        
        content.add_widget(btn_box)
        
        popup = Popup(
            title='确认清空',
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        popup.open()
    
    def go_back(self, instance):
        """返回"""
        self.manager.current = 'pool_list'


class SettingsScreen(Screen):
    """设置页面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # 标题栏
        top_bar = BoxLayout(size_hint_y=0.1, spacing=dp(10))
        
        back_btn = Button(
            text='← 返回',
            font_size=dp(14),
            size_hint_x=0.3,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        back_btn.bind(on_press=self.go_back)
        top_bar.add_widget(back_btn)
        
        title = Label(
            text='⚙️ 设置',
            font_size=dp(20),
            bold=True,
            size_hint_x=0.7
        )
        top_bar.add_widget(title)
        
        layout.add_widget(top_bar)
        
        # 设置列表
        scroll = ScrollView(size_hint=(1, 0.9))
        settings_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        settings_list.bind(minimum_height=settings_list.setter('height'))
        
        # 音效开关
        self.sound_switch = self.create_switch(
            '🔊 音效',
            data_manager.get_setting("sound_enabled", True)
        )
        settings_list.add_widget(self.sound_switch)
        
        # 振动开关
        self.vibration_switch = self.create_switch(
            '📳 振动',
            data_manager.get_setting("vibration_enabled", True)
        )
        settings_list.add_widget(self.vibration_switch)
        
        # 导出数据
        export_btn = Button(
            text='📤 导出数据（JSON）',
            font_size=dp(14),
            size_hint_y=None,
            height=dp(50),
            background_color=(0.3, 0.5, 0.8, 1)
        )
        export_btn.bind(on_press=self.export_data)
        settings_list.add_widget(export_btn)
        
        # 导入数据
        import_btn = Button(
            text='📥 导入数据（JSON）',
            font_size=dp(14),
            size_hint_y=None,
            height=dp(50),
            background_color=(0.3, 0.6, 0.4, 1)
        )
        import_btn.bind(on_press=self.import_data)
        settings_list.add_widget(import_btn)
        
        # 重置数据
        reset_btn = Button(
            text='🗑️ 重置所有数据',
            font_size=dp(14),
            size_hint_y=None,
            height=dp(50),
            background_color=(0.8, 0.2, 0.2, 1)
        )
        reset_btn.bind(on_press=self.confirm_reset)
        settings_list.add_widget(reset_btn)
        
        scroll.add_widget(settings_list)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
    
    def create_switch(self, label_text, active):
        """创建开关设置项"""
        box = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=dp(10)
        )
        
        with box.canvas.before:
            Color(0.2, 0.2, 0.25, 1)
            bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])
        box.bind(pos=lambda *args: setattr(bg, 'pos', box.pos),
                 size=lambda *args: setattr(bg, 'size', box.size))
        
        label = Label(
            text=label_text,
            font_size=dp(14),
            size_hint_x=0.7,
            halign='left',
            valign='middle'
        )
        label.bind(size=label.setter('text_size'))
        box.add_widget(label)
        
        switch_btn = Button(
            text='开' if active else '关',
            font_size=dp(12),
            size_hint_x=0.3,
            background_color=(0.2, 0.7, 0.3, 1) if active else (0.5, 0.5, 0.5, 1)
        )
        
        key = "sound_enabled" if "音效" in label_text else "vibration_enabled"
        
        def toggle(instance):
            current = data_manager.get_setting(key, True)
            new_val = not current
            data_manager.set_setting(key, new_val)
            instance.text = '开' if new_val else '关'
            instance.background_color = (0.2, 0.7, 0.3, 1) if new_val else (0.5, 0.5, 0.5, 1)
        
        switch_btn.bind(on_press=toggle)
        box.add_widget(switch_btn)
        
        return box
    
    def export_data(self, instance):
        """导出数据"""
        data = data_manager.export_data()
        filename = f"lottery_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = DATA_DIR / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            popup = Popup(
                title='导出成功',
                content=Label(text=f'数据已保存到:\n{filepath}', font_size=dp(14)),
                size_hint=(0.8, 0.3)
            )
            popup.open()
        except Exception as e:
            popup = Popup(
                title='导出失败',
                content=Label(text=f'错误: {e}', font_size=dp(14)),
                size_hint=(0.8, 0.3)
            )
            popup.open()
    
    def import_data(self, instance):
        """导入数据（简化版 - 从固定文件导入）"""
        popup = Popup(
            title='导入数据',
            content=Label(
                text='请将备份文件命名为 "import.json"\n放在应用目录下\n然后点击确认',
                font_size=dp(14)
            ),
            size_hint=(0.8, 0.4)
        )
        popup.open()
        
        # 实际导入逻辑
        import_file = DATA_DIR / "import.json"
        if import_file.exists():
            try:
                with open(import_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data_manager.import_data(data)
                popup = Popup(
                    title='导入成功',
                    content=Label(text='数据导入成功！', font_size=dp(16)),
                    size_hint=(0.7, 0.3)
                )
                popup.open()
            except Exception as e:
                popup = Popup(
                    title='导入失败',
                    content=Label(text=f'错误: {e}', font_size=dp(14)),
                    size_hint=(0.8, 0.3)
                )
                popup.open()
    
    def confirm_reset(self, instance):
        """确认重置"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        label = Label(
            text='⚠️ 警告 ⚠️\n\n确定要重置所有数据吗？\n这将删除所有奖池、历史记录和设置！\n此操作不可恢复！',
            font_size=dp(14),
            color=(1, 0.3, 0.3, 1)
        )
        content.add_widget(label)
        
        btn_box = BoxLayout(size_hint_y=0.3, spacing=dp(10))
        
        def confirm(instance):
            data_manager.reset_all()
            popup.dismiss()
            popup2 = Popup(
                title='已重置',
                content=Label(text='所有数据已重置', font_size=dp(16)),
                size_hint=(0.7, 0.3)
            )
            popup2.open()
        
        def cancel(instance):
            popup.dismiss()
        
        reset_btn = Button(text='确认重置', background_color=(0.8, 0.1, 0.1, 1))
        reset_btn.bind(on_press=confirm)
        btn_box.add_widget(reset_btn)
        
        cancel_btn = Button(text='取消', background_color=(0.5, 0.5, 0.5, 1))
        cancel_btn.bind(on_press=cancel)
        btn_box.add_widget(cancel_btn)
        
        content.add_widget(btn_box)
        
        popup = Popup(
            title='危险操作',
            content=content,
            size_hint=(0.9, 0.5),
            auto_dismiss=False
        )
        popup.open()
    
    def go_back(self, instance):
        """返回"""
        self.manager.current = 'pool_list'


# ==================== 主应用 ====================

class LotteryApp(App):
    """双人抽奖 App"""
    
    def build(self):
        """构建应用"""
        # 设置窗口背景色
        Window.clearcolor = (0.1, 0.1, 0.12, 1)
        
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加页面
        sm.add_widget(PoolListScreen())
        sm.add_widget(DrawScreen())
        sm.add_widget(HistoryScreen())
        sm.add_widget(SettingsScreen())
        
        return sm


if __name__ == '__main__':
    LotteryApp().run()

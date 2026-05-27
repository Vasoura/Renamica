#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renamica
批量改名工具 - 支持文件和文件夹改名，支持拖拽，批量替换关键词，增加前缀后缀
"""

import sys
import os
import re
import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QListWidget, QListWidgetItem, QPushButton,
                             QLineEdit, QLabel, QGroupBox, QMessageBox, QProgressBar,
                             QTextEdit, QSplitter, QFrame, QCheckBox, QSpinBox, QComboBox,
                             QFileDialog, QHeaderView, QAction, QMenu, QAbstractItemView, QListView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QUrl, QEvent
from PyQt5.QtGui import QFont, QIcon, QDragEnterEvent, QDropEvent, QColor, QBrush, QDesktopServices

ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*]')
LOG_DIR = Path.home() / '.renamica'
LOG_FILE = LOG_DIR / 'rename_log.csv'
CONFIG_FILE = LOG_DIR / 'config.json'

LOCALE = {
    # --- Worker messages ---
    "file_not_exist": {"zh": "文件不存在", "en": "File does not exist"},
    "skip_not_exist": {"zh": "跳过不存在的文件", "en": "Skipping non-existent"},
    "empty_filename": {"zh": "新文件名为空", "en": "New filename is empty"},
    "skip_empty": {"zh": "新文件名为空", "en": "empty filename"},
    "renaming": {"zh": "重命名", "en": "Renaming"},
    "failed": {"zh": "失败", "en": "Failed"},
    "no_change": {"zh": "无需更改", "en": "No change"},
    "rename_error": {"zh": "重命名过程中发生错误", "en": "Error during rename"},

    # --- GroupBox titles ---
    "file_list": {"zh": "文件列表", "en": "File List"},
    "find_replace": {"zh": "查找替换", "en": "Find & Replace"},
    "delete": {"zh": "删除", "en": "Delete"},
    "prefix_suffix": {"zh": "前缀后缀", "en": "Prefix & Suffix"},
    "numbering": {"zh": "编号", "en": "Numbering"},

    # --- Sort ---
    "sort": {"zh": "排序:", "en": "Sort:"},
    "sort_order": {"zh": "拖入顺序", "en": "Original Order"},
    "sort_name": {"zh": "文件名", "en": "File Name"},
    "sort_mtime": {"zh": "修改时间", "en": "Date Modified"},
    "sort_ctime": {"zh": "创建时间", "en": "Date Created"},
    "sort_size": {"zh": "文件大小", "en": "File Size"},
    "sort_type": {"zh": "文件类型", "en": "File Type"},

    # --- Buttons ---
    "move_up": {"zh": "上移", "en": "Move Up"},
    "move_down": {"zh": "下移", "en": "Move Down"},
    "execute": {"zh": "执行", "en": "Execute"},
    "undo": {"zh": "撤销", "en": "Undo"},
    "clear_list": {"zh": "清空列表", "en": "Clear List"},

    # --- Find & Replace ---
    "find_label": {"zh": "查找:", "en": "Find:"},
    "replace_label": {"zh": "替换:", "en": "Replace:"},
    "find_ph": {"zh": "查找文本", "en": "Search text"},
    "replace_ph": {"zh": "替换文本", "en": "Replace text"},
    "use_regex": {"zh": "使用正则表达式", "en": "Use Regex"},

    # --- Delete ---
    "keyword_label": {"zh": "关键词:", "en": "Keyword:"},
    "keyword_ph": {"zh": "删除", "en": "Delete"},
    "del_check": {"zh": "删从", "en": "Del from"},
    "from_label": {"zh": "", "en": ""},
    "del_label": {"zh": "位删", "en": "del"},
    "pos_label": {"zh": "位", "en": ""},

    # --- Prefix & Suffix ---
    "prefix_label": {"zh": "前缀:", "en": "Prefix:"},
    "suffix_label": {"zh": "后缀:", "en": "Suffix:"},
    "prefix_ph": {"zh": "前缀", "en": "Prefix"},
    "suffix_ph": {"zh": "后缀", "en": "Suffix"},

    # --- Numbering ---
    "enable_numbering": {"zh": "启用编号", "en": "Enable Numbering"},
    "start_label": {"zh": "起始:", "en": "Start:"},
    "digits_label": {"zh": "位数:", "en": "Digits:"},

    # --- Status ---
    "ready": {"zh": "就绪", "en": "Ready"},
    "toggle_dark": {"zh": "切换深色模式", "en": "Toggle Dark Mode"},

    # --- Tip ---
    "tip_drag": {"zh": "提示：可直接拖拽文件或文件夹到列表中", "en": "Tip: Drag files or folders into the list"},

    # --- Conflict ---
    "conflict_label": {"zh": "个问题 — 禁止执行", "en": "issues — Execution blocked"},
    "conflict_empty": {"zh": "新文件名为空", "en": "New filename is empty"},
    "conflict_illegal": {"zh": "包含非法字符", "en": "Contains illegal characters"},
    "conflict_exists": {"zh": "目标文件已存在", "en": "Target already exists"},
    "conflict_duplicate": {"zh": "多个文件重命名为相同名称", "en": "Multiple files map to same name"},

    # --- Tooltip ---
    "tooltip_original": {"zh": "原名", "en": "Original"},
    "tooltip_new": {"zh": "新名", "en": "New"},
    "tooltip_issues": {"zh": "问题", "en": "Issues"},

    # --- Folder import ---
    "import_title": {"zh": "导入文件夹", "en": "Import Folder"},
    "import_question": {"zh": "如何处理文件夹", "en": "How to import folder"},
    "import_path": {"zh": "路径", "en": "Path"},
    "import_choose": {"zh": "选择导入方式：", "en": "Choose import method:"},
    "import_only": {"zh": "仅当前目录文件", "en": "Files in this folder only"},
    "import_recursive": {"zh": "递归添加所有文件", "en": "Add all files recursively"},
    "import_cancel": {"zh": "取消", "en": "Cancel"},

    # --- General status ---
    "added_items": {"zh": "已添加 {} 个项目", "en": "Added {} items"},
    "total_items": {"zh": "共 {} 个项目", "en": "Total {} items"},
    "list_cleared": {"zh": "列表已清空", "en": "List cleared"},
    "renamed_count": {"zh": "重命名完成！处理了 {} 个项目", "en": "Rename complete! Processed {} items"},
    "renamed_with_errors": {"zh": "完成：{} 个重命名，{} 个错误", "en": "Complete: {} renamed, {} errors"},
    "success_count": {"zh": "成功", "en": "Success"},
    "error_count": {"zh": "错误", "en": "Errors"},
    "error_details": {"zh": "错误详情", "en": "Error details"},

    # --- Dialogs ---
    "dlg_warning": {"zh": "警告", "en": "Warning"},
    "dlg_no_files": {"zh": "请先添加文件或文件夹", "en": "Please add files or folders first"},
    "dlg_conflict_title": {"zh": "存在冲突", "en": "Conflicts Found"},
    "dlg_conflict_msg": {"zh": "检测到 {} 个问题，请修复后再执行", "en": "Found {} issues, fix them first"},
    "dlg_confirm_title": {"zh": "确认重命名", "en": "Confirm Rename"},
    "dlg_confirm_msg": {"zh": "确定要重命名 {} 个项目吗？\n此操作可通过「撤销」恢复！", "en": "Rename {} items?\nThis can be undone!"},
    "dlg_undo_title": {"zh": "撤销", "en": "Undo"},
    "dlg_undo_none": {"zh": "没有可撤销的操作", "en": "Nothing to undo"},
    "dlg_undo_result": {"zh": "撤销结果", "en": "Undo Result"},
    "dlg_undo_done": {"zh": "撤销完成！成功恢复 {} 个文件", "en": "Undo complete! Restored {} files"},
    "dlg_undo_fail": {"zh": "原路径已被占用", "en": "Original path is occupied"},
    "dlg_failed": {"zh": "失败", "en": "failed"},
    "dlg_complete": {"zh": "完成", "en": "Complete"},
    "dlg_complete_err": {"zh": "完成（有错误）", "en": "Complete (with errors)"},
    "dlg_processed": {"zh": "处理了 {} 个项目", "en": "Processed {} items"},

    # --- File dialogs ---
    "fd_select_files": {"zh": "选择文件", "en": "Select Files"},
    "fd_all_files": {"zh": "所有文件 (*)", "en": "All Files (*)"},
    "fd_select_folder": {"zh": "选择文件夹", "en": "Select Folder"},

    # --- Log ---
    "log_save_fail": {"zh": "保存日志失败", "en": "Failed to save log"},

    # --- Menu ---
    "menu_file": {"zh": "文件", "en": "File"},
    "menu_edit": {"zh": "编辑", "en": "Edit"},
    "menu_help": {"zh": "帮助", "en": "Help"},
    "menu_add_files": {"zh": "添加文件...", "en": "Add Files..."},
    "menu_add_folder": {"zh": "添加文件夹...", "en": "Add Folder..."},
    "menu_clear": {"zh": "清空列表", "en": "Clear List"},
    "menu_quit": {"zh": "退出", "en": "Quit"},
    "menu_undo": {"zh": "撤销上次重命名", "en": "Undo Last Rename"},
    "menu_github": {"zh": "GitHub", "en": "GitHub"},
    "menu_remove": {"zh": "从列表中移除", "en": "Remove from List"},

    # --- Language toggle ---
    "lang_toggle": {"zh": "中", "en": "EN"},
    "lang_tooltip_cn": {"zh": "切换至英文", "en": "Switch to Chinese"},

    # --- Folder import mode ---
    "folder_import": {"zh": "导入文件夹", "en": "Folder Import"},
    "folder_flat": {"zh": "仅当前目录文件", "en": "Files in folder only"},
    "folder_recursive": {"zh": "递归添加所有文件", "en": "Recursive all files"},

    # --- Progress messages ---
    "progress_renaming": {"zh": "重命名: {} -> {}", "en": "Renaming: {} -> {}"},
    "progress_no_change": {"zh": "无需更改: {}", "en": "No change: {}"},
    "progress_skipped": {"zh": "跳过: {} -> {}", "en": "Skipping: {} -> {}"},
    "progress_failed": {"zh": "失败: {} -> {}", "en": "Failed: {} -> {}"},
}

LANG_KEY = "lang"

def _(key, *args):
    val = LOCALE.get(key, {})
    text = val.get(_current_lang, val.get("zh", key))
    if args:
        text = text.format(*args)
    return text

def detect_system_language():
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleLanguages"],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            out = result.stdout
            if '"zh' in out or '"yue' in out:
                return "zh"
        return "en"
    except Exception:
        return "en"

def load_config():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}

def save_config(config):
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

config = load_config()
_current_lang = config.get(LANG_KEY, detect_system_language())


class DragDropListWidget(QListWidget):
    """支持拖拽的文件列表控件"""

    def __init__(self, parent_gui):
        super().__init__()
        self.parent_gui = parent_gui
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DropOnly)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.exists(file_path):
                files.append(file_path)
        if files:
            self.parent_gui.add_files_to_list(files)
        event.acceptProposedAction()

    def contextMenuEvent(self, event):
        selected_items = self.selectedItems()
        if not selected_items:
            item = self.itemAt(event.pos())
            if not item:
                return
            selected_items = [item]
            
        cursor_item = self.itemAt(event.pos())
        if cursor_item and cursor_item not in selected_items:
            self.clearSelection()
            cursor_item.setSelected(True)
            selected_items = [cursor_item]
            
        rows = [self.row(item) for item in selected_items]
        menu = QMenu(self)
        
        remove_action = QAction(_("menu_remove"), self)
        remove_action.triggered.connect(lambda: self.parent_gui.remove_files_at(rows))
        menu.addAction(remove_action)
        
        menu.exec_(event.globalPos())


def is_path_conflict(candidate_path, file_path, allocated_paths):
    cand_str = str(candidate_path)
    cand_str_lower = cand_str.lower()
    if any(p.lower() == cand_str_lower for p in allocated_paths):
        return True
        
    if candidate_path.exists():
        try:
            if os.path.samefile(cand_str, str(file_path)):
                return False
        except OSError:
            if cand_str_lower == str(file_path).lower():
                return False
        return True
        
    return False


SORT_INDEX_TO_KEY = {
    0: None,
    1: "name",
    2: "mtime",
    3: "ctime",
    4: "size",
    5: "type"
}


def number_to_letter(number, digits, uppercase=False):
    """将数字转换为字母编号"""
    result = ""
    for _ in range(digits):
        remainder = (number - 1) % 26
        result = chr(ord('a' if not uppercase else 'A') + remainder) + result
        number = (number - 1) // 26
        if number == 0:
            number = 1
            break
    return result


class RenameWorker(QThread):
    """重命名工作线程"""
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(list, list)
    file_error = pyqtSignal(int, str)

    def __init__(self, file_paths, resolved_names, rename_options, lang="zh"):
        super().__init__()
        self.file_paths = file_paths
        self.resolved_names = resolved_names
        self.rename_options = rename_options
        self.lang = lang
        self.new_paths = []
        self.mappings = []
        self.error_list = []

    def _tr(self, key):
        return LOCALE.get(key, {}).get(self.lang, LOCALE.get(key, {}).get("zh", key))

    def _tr_fmt(self, key, *args):
        return self._tr(key).format(*args)

    def run(self):
        try:
            total = len(self.file_paths)
            self.new_paths = []
            self.mappings = []
            self.error_list = []

            for i, file_path in enumerate(self.file_paths):
                if not os.path.exists(file_path):
                    msg = f"{self._tr('skip_not_exist')}: {file_path}"
                    self.progress_updated.emit(int((i + 1) / total * 100), msg)
                    self.new_paths.append(file_path)
                    self.mappings.append((file_path, file_path))
                    self.file_error.emit(i, self._tr("file_not_exist"))
                    self.error_list.append((i, self._tr("file_not_exist")))
                    continue

                path_obj = Path(file_path)
                parent_dir = path_obj.parent
                original_name = path_obj.name

                new_name = self.resolved_names[i] if i < len(self.resolved_names) else original_name

                if not new_name or not new_name.strip():
                    msg = f"{self._tr('skip_empty')}: {original_name}"
                    self.progress_updated.emit(int((i + 1) / total * 100), msg)
                    self.new_paths.append(file_path)
                    self.mappings.append((file_path, file_path))
                    self.file_error.emit(i, self._tr("empty_filename"))
                    self.error_list.append((i, self._tr("empty_filename")))
                    continue

                new_path = parent_dir / new_name

                if new_path != path_obj:
                    try:
                        os.rename(str(path_obj), str(new_path))
                        self.progress_updated.emit(int((i + 1) / total * 100),
                                                   self._tr_fmt("progress_renaming", original_name, new_name))
                    except OSError as e:
                        msg = self._tr_fmt("progress_failed", original_name, str(e))
                        self.progress_updated.emit(int((i + 1) / total * 100), msg)
                        self.new_paths.append(file_path)
                        self.mappings.append((file_path, file_path))
                        self.file_error.emit(i, str(e))
                        self.error_list.append((i, str(e)))
                        continue
                else:
                    self.progress_updated.emit(int((i + 1) / total * 100),
                                               self._tr_fmt("progress_no_change", original_name))

                self.new_paths.append(str(new_path))
                self.mappings.append((str(file_path), str(new_path)))

            self.finished.emit(self.new_paths, self.mappings)

        except Exception as e:
            self.file_error.emit(-1, f"{self._tr('rename_error')}: {str(e)}")
            self.finished.emit(self.new_paths, self.mappings)

    def apply_rename_rules(self, original_name, index):
        new_name = original_name

        if self.rename_options['find_text'] and self.rename_options['replace_text'] is not None:
            if self.rename_options['use_regex']:
                try:
                    new_name = re.sub(self.rename_options['find_text'],
                                      self.rename_options['replace_text'], new_name)
                except re.error:
                    new_name = new_name.replace(self.rename_options['find_text'],
                                                self.rename_options['replace_text'])
            else:
                new_name = new_name.replace(self.rename_options['find_text'],
                                            self.rename_options['replace_text'])

        if self.rename_options['delete_text']:
            new_name = new_name.replace(self.rename_options['delete_text'], '')

        if self.rename_options.get('delete_n_enabled'):
            path_obj = Path(new_name)
            stem = path_obj.stem
            suffix = path_obj.suffix
            start = self.rename_options['delete_n_start'] - 1
            count = self.rename_options['delete_n_count']
            if start < len(stem):
                stem = stem[:start] + stem[start + count:]
            new_name = stem + suffix

        if self.rename_options['prefix']:
            new_name = self.rename_options['prefix'] + new_name

        if self.rename_options['suffix']:
            path_obj = Path(new_name)
            stem = path_obj.stem
            suffix = path_obj.suffix
            new_name = stem + self.rename_options['suffix'] + suffix

        if self.rename_options['use_numbering']:
            path_obj = Path(new_name)
            stem = path_obj.stem
            suffix = path_obj.suffix
            number = self.rename_options['start_number'] + index
            digits = self.rename_options.get('number_digits', 3)
            number_type = self.rename_options.get('number_type', 0)
            if number_type == 0:
                number_str = str(number).zfill(digits)
            elif number_type == 1:
                number_str = number_to_letter(number, digits, uppercase=False)
            else:
                number_str = number_to_letter(number, digits, uppercase=True)
            new_name = f"{stem}_{number_str}{suffix}"

        return new_name


class RenamicaGUI(QMainWindow):
    """Renamica 主界面"""

    def __init__(self):
        super().__init__()
        self.file_paths = []
        self.original_file_paths = []
        self.resolved_names = []
        self.rename_history = []
        self.current_errors = {}
        self.current_conflicts = {}
        self.current_sort_key = None
        self.current_sort_ascending = True
        self.is_dark_mode = False
        self.lang = _current_lang
        self._sort_keys = None
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Renamica v1.0.1")
        self.setGeometry(100, 100, 760, 540)

        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        operation_widget = self.create_operation_widget()
        main_layout.addWidget(operation_widget)

        file_widget = self.create_file_list_widget()
        main_layout.addWidget(file_widget)

        self.apply_macOS_style()
        self.connect_preview_signals()

    def retranslate_ui(self):
        """切换语言后刷新所有文本"""
        self.setWindowTitle("Renamica v1.0.1")

        self.file_group.setTitle(_("file_list"))
        self.find_replace_box.setTitle(_("find_replace"))
        self.delete_box.setTitle(_("delete"))
        self.prefix_suffix_box.setTitle(_("prefix_suffix"))
        self.numbering_box.setTitle(_("numbering"))

        self.sort_label.setText(_("sort"))
        current_sort = self.sort_combo.currentIndex()
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        self.sort_combo.addItems([
            _("sort_order"),
            _("sort_name"),
            _("sort_mtime"),
            _("sort_ctime"),
            _("sort_size"),
            _("sort_type")
        ])
        self.sort_combo.setCurrentIndex(current_sort)
        self.sort_combo.blockSignals(False)

        self.move_up_btn.setText(_("move_up"))
        self.move_down_btn.setText(_("move_down"))
        self.execute_btn.setText(_("execute"))
        self.undo_btn.setText(_("undo"))
        self.clear_list_btn.setText(_("clear_list"))

        self.find_label.setText(_("find_label"))
        self.replace_label.setText(_("replace_label"))
        self.find_edit.setPlaceholderText(_("find_ph"))
        self.replace_edit.setPlaceholderText(_("replace_ph"))
        self.regex_checkbox.setText(_("use_regex"))

        self.keyword_label.setText(_("keyword_label"))
        self.delete_edit.setPlaceholderText(_("keyword_ph"))
        self.delete_n_checkbox.setText(_("del_check"))
        self.from_label.setText(_("from_label"))
        self.del_label.setText(_("del_label"))
        self.pos_label.setText(_("pos_label"))

        self.prefix_label.setText(_("prefix_label"))
        self.suffix_label.setText(_("suffix_label"))
        self.prefix_edit.setPlaceholderText(_("prefix_ph"))
        self.suffix_edit.setPlaceholderText(_("suffix_ph"))

        self.numbering_checkbox.setText(_("enable_numbering"))
        self.start_label.setText(_("start_label"))
        self.digits_label.setText(_("digits_label"))

        self.status_label.setText(_("ready"))
        self.dark_mode_btn.setToolTip(_("toggle_dark"))
        self.lang_btn.setToolTip(_("lang_tooltip_cn"))
        self.lang_btn.setText(_("lang_toggle"))
        self.tip_label.setText(_("tip_drag"))

        self.file_menu.setTitle(_("menu_file"))
        self.edit_menu.setTitle(_("menu_edit"))
        self.help_menu.setTitle(_("menu_help"))
        self.add_files_action.setText(_("menu_add_files"))
        self.add_folder_action.setText(_("menu_add_folder"))
        self.clear_action.setText(_("menu_clear"))
        self.quit_action.setText(_("menu_quit"))
        self.undo_menu_action.setText(_("menu_undo"))
        self.github_action.setText(_("menu_github"))
        self.folder_import_menu.setTitle(_("folder_import"))
        self.folder_import_flat.setText(_("folder_flat"))
        self.folder_import_recursive.setText(_("folder_recursive"))

        self.update_sort_combo_text()
        self.update_preview()

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        self.file_menu = menu_bar.addMenu(_("menu_file"))

        self.add_files_action = QAction(_("menu_add_files"), self)
        self.add_files_action.setShortcut("Ctrl+O")
        self.add_files_action.triggered.connect(self.add_files)
        self.file_menu.addAction(self.add_files_action)

        self.add_folder_action = QAction(_("menu_add_folder"), self)
        self.add_folder_action.setShortcut("Ctrl+Shift+O")
        self.add_folder_action.triggered.connect(self.add_folders)
        self.file_menu.addAction(self.add_folder_action)

        self.file_menu.addSeparator()

        self.clear_action = QAction(_("menu_clear"), self)
        self.clear_action.triggered.connect(self.clear_file_list)
        self.file_menu.addAction(self.clear_action)

        self.file_menu.addSeparator()

        self.folder_import_menu = self.file_menu.addMenu(_("folder_import"))

        self.folder_import_flat = QAction(_("folder_flat"), self)
        self.folder_import_flat.setCheckable(True)
        self.folder_import_flat.setChecked(config.get("folder_import_mode", "flat") == "flat")
        self.folder_import_flat.triggered.connect(lambda: self._set_folder_import_mode("flat"))
        self.folder_import_menu.addAction(self.folder_import_flat)

        self.folder_import_recursive = QAction(_("folder_recursive"), self)
        self.folder_import_recursive.setCheckable(True)
        self.folder_import_recursive.setChecked(config.get("folder_import_mode") == "recursive")
        self.folder_import_recursive.triggered.connect(lambda: self._set_folder_import_mode("recursive"))
        self.folder_import_menu.addAction(self.folder_import_recursive)

        self.file_menu.addSeparator()

        self.quit_action = QAction(_("menu_quit"), self)
        self.quit_action.setShortcut("Ctrl+Q")
        self.quit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.quit_action)

        self.edit_menu = menu_bar.addMenu(_("menu_edit"))

        self.undo_menu_action = QAction(_("menu_undo"), self)
        self.undo_menu_action.setShortcut("Ctrl+Z")
        self.undo_menu_action.triggered.connect(self.undo_rename)
        self.undo_menu_action.setEnabled(False)
        self.edit_menu.addAction(self.undo_menu_action)

        self.help_menu = menu_bar.addMenu(_("menu_help"))

        self.github_action = QAction(_("menu_github"), self)
        self.github_action.triggered.connect(self.open_github)
        self.help_menu.addAction(self.github_action)

    def open_github(self):
        QDesktopServices.openUrl(QUrl("https://github.com/Vasoura/Renamica"))

    def create_file_list_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)

        self.file_group = QGroupBox(_("file_list"))
        file_layout = QVBoxLayout(self.file_group)
        file_layout.setSpacing(3)
        file_layout.setContentsMargins(5, 5, 5, 5)

        sort_bar = QHBoxLayout()
        sort_bar.setSpacing(4)

        self.sort_label = QLabel(_("sort"))
        sort_bar.addWidget(self.sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.setView(QListView())
        self.sort_combo.addItems([
            _("sort_order"),
            _("sort_name"),
            _("sort_mtime"),
            _("sort_ctime"),
            _("sort_size"),
            _("sort_type")
        ])
        self.sort_combo.setMaximumHeight(24)
        self.sort_combo.setFixedWidth(120)
        self.sort_combo.activated.connect(self.on_sort_combo_activated)
        sort_bar.addWidget(self.sort_combo)

        sort_bar.addStretch()

        self.move_up_btn = QPushButton(_("move_up"))
        self.move_up_btn.setMaximumHeight(24)
        self.move_up_btn.clicked.connect(self.move_item_up)
        sort_bar.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton(_("move_down"))
        self.move_down_btn.setMaximumHeight(24)
        self.move_down_btn.clicked.connect(self.move_item_down)
        sort_bar.addWidget(self.move_down_btn)

        file_layout.addLayout(sort_bar)

        self.file_list = DragDropListWidget(self)
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        file_layout.addWidget(self.file_list)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        self.execute_btn = QPushButton(_("execute"))
        self.execute_btn.clicked.connect(self.execute_rename)
        self.execute_btn.setMaximumHeight(25)
        button_layout.addWidget(self.execute_btn)

        self.undo_btn = QPushButton(_("undo"))
        self.undo_btn.clicked.connect(self.undo_rename)
        self.undo_btn.setMaximumHeight(25)
        self.undo_btn.setEnabled(False)
        button_layout.addWidget(self.undo_btn)

        self.clear_list_btn = QPushButton(_("clear_list"))
        self.clear_list_btn.clicked.connect(self.clear_file_list)
        self.clear_list_btn.setMaximumHeight(25)
        button_layout.addWidget(self.clear_list_btn)

        file_layout.addLayout(button_layout)
        layout.addWidget(self.file_group)

        self.status_bar = QHBoxLayout()
        self.conflict_label = QLabel("")
        self.conflict_label.setStyleSheet("color: #dc3545; font-size: 11px; padding: 2px 5px;")
        self.status_bar.addWidget(self.conflict_label)
        self.status_bar.addStretch()

        self.tip_label = QLabel(_("tip_drag"))
        self.tip_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        self.status_bar.addWidget(self.tip_label)

        layout.addLayout(self.status_bar)

        return widget

    def connect_preview_signals(self):
        self.find_edit.textChanged.connect(self.update_preview)
        self.replace_edit.textChanged.connect(self.update_preview)
        self.regex_checkbox.stateChanged.connect(self.update_preview)
        self.delete_edit.textChanged.connect(self.update_preview)
        self.delete_n_checkbox.stateChanged.connect(self.update_preview)
        self.delete_n_start.valueChanged.connect(self.update_preview)
        self.delete_n_count.valueChanged.connect(self.update_preview)
        self.prefix_edit.textChanged.connect(self.update_preview)
        self.suffix_edit.textChanged.connect(self.update_preview)
        self.numbering_checkbox.stateChanged.connect(self.update_preview)
        self.start_value_edit.textChanged.connect(self.update_preview)
        self.number_digits_spin.valueChanged.connect(self.update_preview)

    def create_operation_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        rename_layout = QHBoxLayout()
        rename_layout.setSpacing(10)
        rename_layout.setContentsMargins(0, 0, 0, 0)

        self.find_replace_box = QGroupBox(_("find_replace"))
        self.find_replace_box.setObjectName("sub_group")
        find_replace_inner = QVBoxLayout(self.find_replace_box)
        find_replace_inner.setSpacing(4)
        find_replace_inner.setContentsMargins(8, 12, 8, 8)

        find_layout = QHBoxLayout()
        self.find_label = QLabel(_("find_label"))
        find_layout.addWidget(self.find_label)
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText(_("find_ph"))
        self.find_edit.setMinimumHeight(26)
        self.find_edit.setMaximumHeight(28)
        find_layout.addWidget(self.find_edit)
        find_replace_inner.addLayout(find_layout)

        replace_layout = QHBoxLayout()
        self.replace_label = QLabel(_("replace_label"))
        replace_layout.addWidget(self.replace_label)
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText(_("replace_ph"))
        self.replace_edit.setMinimumHeight(26)
        self.replace_edit.setMaximumHeight(28)
        replace_layout.addWidget(self.replace_edit)
        find_replace_inner.addLayout(replace_layout)

        self.regex_checkbox = QCheckBox(_("use_regex"))
        find_replace_inner.addWidget(self.regex_checkbox)

        rename_layout.addWidget(self.find_replace_box)

        self.delete_box = QGroupBox(_("delete"))
        self.delete_box.setObjectName("sub_group")
        delete_inner = QVBoxLayout(self.delete_box)
        delete_inner.setSpacing(4)
        delete_inner.setContentsMargins(6, 10, 6, 6)

        delete_input_layout = QHBoxLayout()
        self.keyword_label = QLabel(_("keyword_label"))
        delete_input_layout.addWidget(self.keyword_label)
        self.delete_edit = QLineEdit()
        self.delete_edit.setPlaceholderText(_("keyword_ph"))
        self.delete_edit.setMinimumHeight(24)
        self.delete_edit.setMaximumHeight(26)
        self.delete_edit.setMaximumWidth(100)
        delete_input_layout.addWidget(self.delete_edit)
        delete_inner.addLayout(delete_input_layout)

        delete_n_layout = QHBoxLayout()
        delete_n_layout.setSpacing(6)
        self.delete_n_checkbox = QCheckBox(_("del_check"))
        self.delete_n_checkbox.setMinimumHeight(24)
        delete_n_layout.addWidget(self.delete_n_checkbox)

        self.from_label = QLabel(_("from_label"))
        delete_n_layout.addWidget(self.from_label)
        self.delete_n_start = QSpinBox()
        self.delete_n_start.setMinimum(1)
        self.delete_n_start.setMaximum(999)
        self.delete_n_start.setValue(1)
        self.delete_n_start.setMinimumHeight(24)
        self.delete_n_start.setMaximumWidth(45)
        delete_n_layout.addWidget(self.delete_n_start)

        self.del_label = QLabel(_("del_label"))
        delete_n_layout.addWidget(self.del_label)
        self.delete_n_count = QSpinBox()
        self.delete_n_count.setMinimum(1)
        self.delete_n_count.setMaximum(999)
        self.delete_n_count.setValue(1)
        self.delete_n_count.setMinimumHeight(24)
        self.delete_n_count.setMaximumWidth(45)
        delete_n_layout.addWidget(self.delete_n_count)

        self.pos_label = QLabel(_("pos_label"))
        delete_n_layout.addWidget(self.pos_label)
        delete_n_layout.addStretch()
        delete_inner.addLayout(delete_n_layout)

        rename_layout.addWidget(self.delete_box)

        self.prefix_suffix_box = QGroupBox(_("prefix_suffix"))
        self.prefix_suffix_box.setObjectName("sub_group")
        prefix_suffix_inner = QVBoxLayout(self.prefix_suffix_box)
        prefix_suffix_inner.setSpacing(4)
        prefix_suffix_inner.setContentsMargins(8, 12, 8, 8)

        prefix_layout = QHBoxLayout()
        self.prefix_label = QLabel(_("prefix_label"))
        prefix_layout.addWidget(self.prefix_label)
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText(_("prefix_ph"))
        self.prefix_edit.setMinimumHeight(26)
        self.prefix_edit.setMaximumHeight(28)
        self.prefix_edit.setMaximumWidth(80)
        prefix_layout.addWidget(self.prefix_edit)
        prefix_suffix_inner.addLayout(prefix_layout)

        suffix_layout = QHBoxLayout()
        self.suffix_label = QLabel(_("suffix_label"))
        suffix_layout.addWidget(self.suffix_label)
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setPlaceholderText(_("suffix_ph"))
        self.suffix_edit.setMinimumHeight(26)
        self.suffix_edit.setMaximumHeight(28)
        self.suffix_edit.setMaximumWidth(80)
        suffix_layout.addWidget(self.suffix_edit)
        prefix_suffix_inner.addLayout(suffix_layout)

        rename_layout.addWidget(self.prefix_suffix_box)

        self.numbering_box = QGroupBox(_("numbering"))
        self.numbering_box.setObjectName("sub_group")
        numbering_inner = QVBoxLayout(self.numbering_box)
        numbering_inner.setSpacing(4)
        numbering_inner.setContentsMargins(6, 10, 6, 6)

        self.numbering_checkbox = QCheckBox(_("enable_numbering"))
        self.numbering_checkbox.setMinimumHeight(24)
        numbering_inner.addWidget(self.numbering_checkbox)

        number_options_layout = QHBoxLayout()
        self.start_label = QLabel(_("start_label"))
        number_options_layout.addWidget(self.start_label)
        self.start_value_edit = QLineEdit()
        self.start_value_edit.setText("1")
        self.start_value_edit.setPlaceholderText("1")
        self.start_value_edit.setMinimumHeight(24)
        self.start_value_edit.setMaximumWidth(45)
        number_options_layout.addWidget(self.start_value_edit)

        self.digits_label = QLabel(_("digits_label"))
        number_options_layout.addWidget(self.digits_label)
        self.number_digits_spin = QSpinBox()
        self.number_digits_spin.setMinimum(1)
        self.number_digits_spin.setMaximum(6)
        self.number_digits_spin.setValue(3)
        self.number_digits_spin.setMinimumHeight(24)
        self.number_digits_spin.setMaximumWidth(45)
        number_options_layout.addWidget(self.number_digits_spin)
        number_options_layout.addStretch()
        numbering_inner.addLayout(number_options_layout)

        rename_layout.addWidget(self.numbering_box)

        layout.addLayout(rename_layout)

        status_container = QWidget()
        status_container.setObjectName("status_container")
        status_layout = QHBoxLayout(status_container)
        status_layout.setSpacing(5)
        status_layout.setContentsMargins(0, 6, 0, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(14)
        status_layout.addWidget(self.progress_bar)

        self.status_label = QLabel(_("ready"))
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        status_layout.addWidget(self.status_label)

        self.lang_btn = QPushButton()
        self.lang_btn.setText(_("lang_toggle"))
        self.lang_btn.setMaximumWidth(32)
        self.lang_btn.setMaximumHeight(24)
        self.lang_btn.setToolTip(_("lang_tooltip_cn"))
        self.lang_btn.clicked.connect(self.on_toggle_language)
        status_layout.addWidget(self.lang_btn)

        self.dark_mode_btn = QPushButton()
        self.dark_mode_btn.setText("🌙")
        self.dark_mode_btn.setMaximumWidth(32)
        self.dark_mode_btn.setMaximumHeight(24)
        self.dark_mode_btn.setToolTip(_("toggle_dark"))
        self.dark_mode_btn.clicked.connect(self.on_toggle_dark_mode)
        status_layout.addWidget(self.dark_mode_btn)

        layout.addWidget(status_container)

        return widget

    def on_toggle_language(self):
        self.lang = "en" if self.lang == "zh" else "zh"
        global _current_lang
        _current_lang = self.lang
        config[LANG_KEY] = self.lang
        save_config(config)
        self.retranslate_ui()

    def _set_folder_import_mode(self, mode):
        config["folder_import_mode"] = mode
        save_config(config)
        self.folder_import_flat.setChecked(mode == "flat")
        self.folder_import_recursive.setChecked(mode == "recursive")

    def update_preview(self):
        if not self.file_paths:
            self.conflict_label.setText("")
            self.resolved_names = []
            return

        self.resolved_names = self.calculate_resolved_names()
        conflicts = self.check_rename_conflicts()
        self.current_conflicts = conflicts

        for i in range(len(self.file_paths)):
            self.update_single_item_preview(i, conflicts)

        if conflicts['has_conflict']:
            self.conflict_label.setText(f"⚠ {conflicts['total']} {_('conflict_label')}")
            self.execute_btn.setEnabled(False)
        else:
            self.conflict_label.setText("")
            self.execute_btn.setEnabled(True)

    def update_single_item_preview(self, index, conflicts=None):
        if index < 0 or index >= len(self.file_paths):
            return

        file_path = self.file_paths[index]
        path_obj = Path(file_path)
        original_name = path_obj.name
        new_name = self.resolved_names[index] if index < len(self.resolved_names) else original_name

        item = self.file_list.item(index)
        if item is None:
            item = QListWidgetItem()
            self.file_list.insertItem(index, item)

        icon = "📁" if os.path.isdir(file_path) else "📄"
        if os.path.isdir(file_path):
            display_name = os.path.basename(file_path.rstrip('/'))
        else:
            display_name = original_name
        original_display = f"{icon} {display_name}"

        tooltip_parts = [f"{_('tooltip_original')}: {original_name}", f"{_('tooltip_new')}: {new_name}"]

        if original_name != new_name:
            item.setText(f"{original_display}  →  {new_name}")
        else:
            item.setText(f"{original_display}")

        has_error = False

        if conflicts:
            file_issues = conflicts.get('file_conflicts', {}).get(index, [])
            if file_issues:
                has_error = True
                tooltip_parts.append("")
                tooltip_parts.append(f"{_('tooltip_issues')}:")
                for issue in file_issues:
                    tooltip_parts.append(f"  ⚠ {issue}")

        item.setToolTip("\n".join(tooltip_parts))

        if has_error:
            item.setForeground(QBrush(QColor("#dc3545")))
        else:
            item.setForeground(QBrush(QColor("#1d1d1f")))

    def apply_rename_rules_preview(self, original_name, original_path, rename_options, index):
        new_name = original_name

        if rename_options['find_text'] and rename_options['replace_text'] is not None:
            if rename_options['use_regex']:
                try:
                    new_name = re.sub(rename_options['find_text'],
                                      rename_options['replace_text'], new_name)
                except re.error:
                    new_name = new_name.replace(rename_options['find_text'],
                                                rename_options['replace_text'])
            else:
                new_name = new_name.replace(rename_options['find_text'],
                                            rename_options['replace_text'])

        if rename_options['delete_text']:
            new_name = new_name.replace(rename_options['delete_text'], '')

        if rename_options.get('delete_n_enabled'):
            path_obj = Path(new_name)
            stem = path_obj.stem
            suffix = path_obj.suffix
            start = rename_options['delete_n_start'] - 1
            count = rename_options['delete_n_count']
            if start < len(stem):
                stem = stem[:start] + stem[start + count:]
            new_name = stem + suffix

        if rename_options['prefix']:
            new_name = rename_options['prefix'] + new_name

        if rename_options['suffix']:
            path_obj = Path(new_name)
            stem = path_obj.stem
            suffix = path_obj.suffix
            new_name = stem + rename_options['suffix'] + suffix

        if rename_options['use_numbering']:
            path_obj = Path(new_name)
            stem = path_obj.stem
            suffix = path_obj.suffix
            number = rename_options['start_number'] + index
            digits = rename_options.get('number_digits', 3)
            number_type = rename_options.get('number_type', 0)
            if number_type == 0:
                number_str = str(number).zfill(digits)
            elif number_type == 1:
                number_str = number_to_letter(number, digits, uppercase=False)
            else:
                number_str = number_to_letter(number, digits, uppercase=True)
            new_name = f"{stem}_{number_str}{suffix}"

        return new_name

    def calculate_resolved_names(self):
        resolved_names = []
        if not self.file_paths:
            return resolved_names

        rename_options = self.get_rename_options()
        allocated_paths = set()

        for i, file_path in enumerate(self.file_paths):
            original_name = Path(file_path).name
            base_new_name = self.apply_rename_rules_preview(original_name, file_path, rename_options, i)
            
            if not base_new_name or not base_new_name.strip() or ILLEGAL_CHARS.search(base_new_name):
                resolved_names.append(base_new_name)
                if base_new_name:
                    allocated_paths.add(str(Path(file_path).parent / base_new_name))
                continue

            parent_dir = Path(file_path).parent
            new_name = base_new_name
            new_path = parent_dir / new_name

            if is_path_conflict(new_path, file_path, allocated_paths):
                path_obj = Path(new_name)
                stem = path_obj.stem
                suffix = path_obj.suffix
                counter = 1
                while True:
                    candidate_name = f"{stem}_{counter}{suffix}"
                    candidate_path = parent_dir / candidate_name
                    if not is_path_conflict(candidate_path, file_path, allocated_paths):
                        new_name = candidate_name
                        new_path = candidate_path
                        break
                    counter += 1

            allocated_paths.add(str(new_path))
            resolved_names.append(new_name)

        return resolved_names

    def check_rename_conflicts(self):
        conflicts = {
            'has_conflict': False,
            'total': 0,
            'file_conflicts': {},
        }
        if not self.file_paths:
            return conflicts

        for i, file_path in enumerate(self.file_paths):
            new_name = self.resolved_names[i] if i < len(self.resolved_names) else ""
            issues = []

            if not new_name or not new_name.strip():
                issues.append(_("conflict_empty"))
            elif ILLEGAL_CHARS.search(new_name):
                illegal = ILLEGAL_CHARS.findall(new_name)
                issues.append(f"{_('conflict_illegal')}: {', '.join(set(illegal))}")

            if issues:
                conflicts['file_conflicts'][i] = issues

        total = sum(len(v) for v in conflicts['file_conflicts'].values())
        conflicts['total'] = total
        conflicts['has_conflict'] = total > 0

        return conflicts

    def on_sort_combo_activated(self, index):
        key = SORT_INDEX_TO_KEY.get(index)
        if key == self.current_sort_key and key is not None:
            self.current_sort_ascending = not self.current_sort_ascending
        else:
            self.current_sort_key = key
            self.current_sort_ascending = True

        self.sort_files_by_type(self.current_sort_key, self.current_sort_ascending)
        self.update_sort_combo_text()

    def update_sort_combo_text(self):
        self.sort_combo.blockSignals(True)
        keys = ["sort_order", "sort_name", "sort_mtime", "sort_ctime", "sort_size", "sort_type"]
        for idx, key in enumerate(keys):
            base_text = _(key)
            if key == "sort_order":
                self.sort_combo.setItemText(idx, base_text)
            else:
                associated_key = SORT_INDEX_TO_KEY.get(idx)
                if associated_key == self.current_sort_key:
                    arrow = " ↑" if self.current_sort_ascending else " ↓"
                    self.sort_combo.setItemText(idx, base_text + arrow)
                else:
                    self.sort_combo.setItemText(idx, base_text)
        self.sort_combo.blockSignals(False)

    def sort_files_by_type(self, sort_type, ascending=True):
        if len(self.file_paths) < 2:
            return

        reverse = not ascending

        if sort_type is None:
            key_func = lambda x: self.original_file_paths.index(x[0]) if x[0] in self.original_file_paths else 999999
            file_infos = [(path, None) for path in self.file_paths]
        else:
            file_infos = []
            for path in self.file_paths:
                try:
                    stat = os.stat(path)
                    file_infos.append((path, stat))
                except OSError:
                    file_infos.append((path, None))

            if sort_type == "name":
                key_func = lambda x: os.path.basename(x[0]).lower()
            elif sort_type == "mtime":
                key_func = lambda x: x[1].st_mtime if x[1] else 0
            elif sort_type == "ctime":
                key_func = lambda x: x[1].st_birthtime if x[1] else 0
            elif sort_type == "size":
                key_func = lambda x: x[1].st_size if x[1] else 0
            elif sort_type == "type":
                key_func = lambda x: Path(x[0]).suffix.lower()
            else:
                return

        file_infos.sort(key=key_func, reverse=reverse)
        self.file_paths = [info[0] for info in file_infos]
        self.file_list.clear()
        self.update_preview()

    def move_item_up(self):
        current_row = self.file_list.currentRow()
        if current_row <= 0:
            return
        self.file_paths[current_row], self.file_paths[current_row - 1] = \
            self.file_paths[current_row - 1], self.file_paths[current_row]
        self.original_file_paths = self.file_paths.copy()

        self.current_sort_key = None
        self.current_sort_ascending = True

        self.sort_combo.blockSignals(True)
        self.sort_combo.setCurrentIndex(0)
        self.sort_combo.blockSignals(False)
        self.update_sort_combo_text()

        self.file_list.clear()
        self.update_preview()
        self.file_list.setCurrentRow(current_row - 1)

    def move_item_down(self):
        current_row = self.file_list.currentRow()
        if current_row < 0 or current_row >= len(self.file_paths) - 1:
            return
        self.file_paths[current_row], self.file_paths[current_row + 1] = \
            self.file_paths[current_row + 1], self.file_paths[current_row]
        self.original_file_paths = self.file_paths.copy()

        self.current_sort_key = None
        self.current_sort_ascending = True

        self.sort_combo.blockSignals(True)
        self.sort_combo.setCurrentIndex(0)
        self.sort_combo.blockSignals(False)
        self.update_sort_combo_text()

        self.file_list.clear()
        self.update_preview()
        self.file_list.setCurrentRow(current_row + 1)

    def undo_rename(self):
        if not self.rename_history:
            self.update_status(_("dlg_undo_none"))
            return

        success_count = 0
        fail_count = 0
        errors = []
        restored_paths = []

        for old_path, new_path in self.rename_history:
            if old_path == new_path:
                restored_paths.append(old_path)
                continue
            if os.path.exists(new_path) and not os.path.exists(old_path):
                try:
                    os.rename(new_path, old_path)
                    success_count += 1
                    restored_paths.append(old_path)
                except OSError as e:
                    fail_count += 1
                    restored_paths.append(new_path)
                    errors.append(f"{os.path.basename(new_path)}: {e}")
            else:
                fail_count += 1
                restored_paths.append(new_path)
                errors.append(f"{os.path.basename(new_path)}: {_('dlg_undo_fail')}")

        self.rename_history = []
        self.undo_btn.setEnabled(False)
        self.undo_menu_action.setEnabled(False)
        self.file_paths = restored_paths

        if fail_count > 0:
            msg = _("dlg_undo_done", success_count)
            msg += f"，{_('dlg_failed')} {fail_count}"
            if errors:
                msg += "\n\n" + "\n".join(errors[:5])
            QMessageBox.warning(self, _("dlg_undo_result"), msg)

        self.refresh_file_list()

    def refresh_file_list(self):
        self.file_list.clear()
        self.update_preview()
        self.update_status(_("total_items", len(self.file_paths)))

    def remove_files_at(self, indices):
        for index in sorted(indices, reverse=True):
            if 0 <= index < len(self.file_paths):
                path = self.file_paths.pop(index)
                if path in self.original_file_paths:
                    self.original_file_paths.remove(path)
        self.refresh_file_list()

    def save_rename_log(self, mappings):
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file_exists = LOG_FILE.exists()

            with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["time", "old_path", "new_path", "status"])
                for old_path, new_path in mappings:
                    status = "success" if old_path != new_path else "skipped"
                    writer.writerow([timestamp, old_path, new_path, status])
        except OSError as e:
            print(f"{_('log_save_fail')}: {e}")

    def apply_macOS_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f5;
            }
            QGroupBox {
                font-weight: 500;
                font-size: 11px;
                border: 1px solid #d1d1d6;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                padding-bottom: 6px;
                background-color: rgba(255, 255, 255, 0.7);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 6px 0 6px;
                color: #1d1d1f;
            }
            QGroupBox#sub_group {
                font-weight: 500;
                font-size: 11px;
                border: 1px solid #e0e0e5;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
                padding-bottom: 4px;
                background-color: rgba(255, 255, 255, 0.5);
            }
            QGroupBox#sub_group::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 4px 0 4px;
                color: #555555;
            }
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #e8e8ed);
                border: 1px solid #c0c0c5;
                color: #1d1d1f;
                padding: 4px 12px;
                text-align: center;
                font-size: 11px;
                border-radius: 5px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f5f5f7, stop: 1 #e0e0e5);
                border: 1px solid #a0a0a5;
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e0e0e5, stop: 1 #d0d0d5);
                border: 1px solid #808085;
            }
            QPushButton:disabled {
                background-color: #f5f5f7;
                color: #999999;
                border: 1px solid #d0d0d5;
            }
            QLineEdit {
                padding: 4px 8px;
                border: 1px solid #d1d1d6;
                border-radius: 5px;
                font-size: 11px;
                background-color: rgba(255, 255, 255, 0.9);
            }
            QLineEdit:focus {
                border: 2px solid #007aff;
                background-color: white;
            }
            QListWidget {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.9);
                selection-background-color: #007aff;
                font-size: 11px;
                padding: 3px;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #007aff;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: rgba(0, 122, 255, 0.1);
            }
            QTextEdit {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.9);
                font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
                font-size: 10px;
                padding: 6px;
            }
            QCheckBox {
                color: #1d1d1f;
                font-size: 11px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid #d1d1d6;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #007aff;
                background-color: #007aff;
                image: none;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #007aff;
            }
            QSpinBox {
                padding: 3px 6px;
                border: 1px solid #d1d1d6;
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 0.9);
                font-size: 11px;
            }
            QSpinBox:focus {
                border: 2px solid #007aff;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background-color: transparent;
            }
            QLabel {
                color: #1d1d1f;
                font-size: 11px;
            }
            QProgressBar {
                border: none;
                border-radius: 5px;
                text-align: center;
                background-color: rgba(0, 0, 0, 0.1);
                min-height: 10px;
            }
            QProgressBar::chunk {
                background-color: #007aff;
                border-radius: 6px;
            }
            QComboBox {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #e8e8ed);
                border: 1px solid #c0c0c5;
                color: #1d1d1f;
                padding: 3px 8px;
                border-radius: 5px;
                font-size: 11px;
                min-height: 22px;
            }
            QComboBox:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f5f5f7, stop: 1 #e0e0e5);
                border: 1px solid #a0a0a5;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #1d1d1f;
                border: 1px solid #d1d1d6;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                color: #1d1d1f;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #007aff;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #007aff;
                color: white;
            }
            QComboBox:focus {
                border: 2px solid #007aff;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #666;
                width: 0px;
                height: 0px;
            }
            QWidget#status_container {
                background-color: rgba(0, 0, 0, 0.03);
                border-top: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)

    def toggle_dark_mode(self, dark_mode):
        if dark_mode:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                }
                QGroupBox {
                    font-weight: 500;
                    font-size: 11px;
                    border: 1px solid #3d3d3d;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 16px;
                    padding-bottom: 6px;
                    background-color: rgba(45, 45, 45, 0.8);
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 12px;
                    padding: 0 6px 0 6px;
                    color: #f5f5f7;
                }
                QGroupBox#sub_group {
                    font-weight: 500;
                    font-size: 11px;
                    border: 1px solid #4a4a4c;
                    border-radius: 6px;
                    margin-top: 8px;
                    padding-top: 10px;
                    padding-bottom: 4px;
                    background-color: rgba(35, 35, 35, 0.6);
                }
                QGroupBox#sub_group::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 10px;
                    padding: 0 4px 0 4px;
                    color: #aaaaaa;
                }
                QPushButton {
                    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #3a3a3c, stop: 1 #2c2c2e);
                    border: 1px solid #5a5a5c;
                    color: #f5f5f7;
                    padding: 4px 12px;
                    text-align: center;
                    font-size: 11px;
                    border-radius: 5px;
                    min-height: 22px;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #4a4a4c, stop: 1 #3c3c3e);
                    border: 1px solid #6a6a6c;
                }
                QPushButton:pressed {
                    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #2c2c2e, stop: 1 #1c1c1e);
                    border: 1px solid #4a4a4c;
                }
                QPushButton:disabled {
                    background-color: #2c2c2e;
                    color: #666666;
                    border: 1px solid #3d3d3d;
                }
                QLineEdit {
                    padding: 4px 8px;
                    border: 1px solid #3d3d3d;
                    border-radius: 5px;
                    font-size: 11px;
                    background-color: rgba(30, 30, 30, 0.9);
                    color: #f5f5f7;
                }
                QLineEdit:focus {
                    border: 2px solid #0a84ff;
                    background-color: #2c2c2e;
                }
                QListWidget {
                    border: 1px solid #3d3d3d;
                    border-radius: 6px;
                    background-color: rgba(30, 30, 30, 0.9);
                    selection-background-color: #0a84ff;
                    font-size: 11px;
                    color: #f5f5f7;
                    padding: 3px;
                }
                QListWidget::item {
                    padding: 4px 6px;
                    border-radius: 3px;
                }
                QListWidget::item:selected {
                    background-color: #0a84ff;
                    color: white;
                }
                QListWidget::item:hover:!selected {
                    background-color: rgba(10, 132, 255, 0.2);
                }
                QCheckBox {
                    color: #f5f5f7;
                    font-size: 11px;
                    spacing: 6px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border-radius: 3px;
                    border: 2px solid #5a5a5c;
                    background-color: #2c2c2e;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #0a84ff;
                    background-color: #0a84ff;
                    image: none;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #0a84ff;
                }
                QSpinBox {
                    padding: 3px 6px;
                    border: 1px solid #3d3d3d;
                    border-radius: 5px;
                    background-color: rgba(30, 30, 30, 0.9);
                    font-size: 11px;
                    color: #f5f5f7;
                }
                QSpinBox:focus {
                    border: 2px solid #0a84ff;
                }
                QLabel {
                    color: #f5f5f7;
                    font-size: 11px;
                }
                QProgressBar {
                    border: none;
                    border-radius: 5px;
                    text-align: center;
                    background-color: rgba(255, 255, 255, 0.1);
                    min-height: 10px;
                }
                QProgressBar::chunk {
                    background-color: #0a84ff;
                    border-radius: 6px;
                }
                QComboBox {
                    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #3a3a3c, stop: 1 #2c2c2e);
                    border: 1px solid #5a5a5c;
                    color: #f5f5f7;
                    padding: 3px 8px;
                    border-radius: 5px;
                    font-size: 11px;
                    min-height: 22px;
                }
                QComboBox:hover {
                    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #4a4a4c, stop: 1 #3c3c3e);
                    border: 1px solid #6a6a6c;
                }
                QComboBox QAbstractItemView {
                    background-color: #2c2c2e;
                    color: #f5f5f7;
                    border: 1px solid #3d3d3d;
                }
                QComboBox QAbstractItemView::item {
                    padding: 4px 8px;
                    color: #f5f5f7;
                }
                QComboBox QAbstractItemView::item:selected {
                    background-color: #0a84ff;
                    color: white;
                }
                QComboBox QAbstractItemView::item:hover {
                    background-color: #0a84ff;
                    color: white;
                }
                QComboBox:focus {
                    border: 2px solid #0a84ff;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 18px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 6px solid #aaa;
                    width: 0px;
                    height: 0px;
                }
                QWidget#status_container {
                    background-color: rgba(0, 0, 0, 0.2);
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                }
            """)
        else:
            self.apply_macOS_style()

    def on_toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.toggle_dark_mode(self.is_dark_mode)
        self.dark_mode_btn.setText("☀️" if self.is_dark_mode else "🌙")

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, _("fd_select_files"), "", _("fd_all_files"))
        if files:
            self.add_files_to_list(files)

    def add_folders(self):
        folder = QFileDialog.getExistingDirectory(self, _("fd_select_folder"))
        if folder:
            self.add_files_to_list([folder])

    def add_files_to_list(self, file_paths):
        resolved = []
        for file_path in file_paths:
            if os.path.isdir(file_path):
                result = self._resolve_folder_import(file_path)
                if result is None:
                    continue
                resolved.extend(result)
            else:
                if file_path not in self.file_paths:
                    resolved.append(file_path)

        if not resolved:
            return

        for p in resolved:
            if p not in self.file_paths:
                self.file_paths.append(p)
                self.original_file_paths.append(p)

        self.file_list.clear()
        self.update_preview()
        self.update_status(_("added_items", len(self.file_paths)))

    def _resolve_folder_import(self, folder_path):
        mode = config.get("folder_import_mode", "flat")

        files = []
        if mode == "recursive":
            for root, dirs, filenames in os.walk(folder_path):
                for f in filenames:
                    files.append(os.path.join(root, f))
        else:
            for entry in os.listdir(folder_path):
                full_path = os.path.join(folder_path, entry)
                if os.path.isfile(full_path):
                    files.append(full_path)
        return files

    def clear_file_list(self):
        self.file_paths.clear()
        self.original_file_paths.clear()
        self.resolved_names.clear()
        self.file_list.clear()
        self.current_conflicts = {}
        self.conflict_label.setText("")
        self.execute_btn.setEnabled(True)
        self.update_status(_("list_cleared"))

    def get_rename_options(self):
        start_text = self.start_value_edit.text().strip()
        start_num, number_type = self.parse_start_value(start_text)

        return {
            'find_text': self.find_edit.text(),
            'replace_text': self.replace_edit.text(),
            'use_regex': self.regex_checkbox.isChecked(),
            'delete_text': self.delete_edit.text(),
            'delete_n_enabled': self.delete_n_checkbox.isChecked(),
            'delete_n_start': self.delete_n_start.value(),
            'delete_n_count': self.delete_n_count.value(),
            'prefix': self.prefix_edit.text(),
            'suffix': self.suffix_edit.text(),
            'use_numbering': self.numbering_checkbox.isChecked(),
            'start_number': start_num,
            'number_type': number_type,
            'number_digits': self.number_digits_spin.value(),
        }

    def parse_start_value(self, text):
        if not text:
            return 1, 0
        text = text.strip()
        if text.isdigit():
            return int(text), 0
        if text.isalpha() and text.islower():
            return self.letter_to_number(text), 1
        if text.isalpha() and text.isupper():
            return self.letter_to_number(text), 2
        try:
            return int(text), 0
        except ValueError:
            return 1, 0

    def letter_to_number(self, letters):
        result = 0
        for char in letters.lower():
            result = result * 26 + (ord(char) - ord('a') + 1)
        return result

    def execute_rename(self):
        if not self.file_paths:
            QMessageBox.warning(self, _("dlg_warning"), _("dlg_no_files"))
            return

        self.resolved_names = self.calculate_resolved_names()
        conflicts = self.check_rename_conflicts()
        if conflicts['has_conflict']:
            QMessageBox.warning(self, _("dlg_conflict_title"),
                                _("dlg_conflict_msg", conflicts['total']))
            return

        self.current_errors = {}

        self.execute_btn.setEnabled(False)
        self.undo_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        options = self.get_rename_options()
        self.worker = RenameWorker(self.file_paths.copy(), self.resolved_names.copy(), options, lang=self.lang)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_rename_finished)
        self.worker.file_error.connect(self.on_file_error)
        self.worker.start()

    def on_progress_updated(self, progress, message):
        self.progress_bar.setValue(progress)
        self.update_status(message)

    def on_file_error(self, index, error_message):
        self.current_errors[index] = error_message

    def on_rename_finished(self, new_paths, mappings):
        self.progress_bar.setVisible(False)
        self.execute_btn.setEnabled(True)

        self.file_paths = new_paths
        self.rename_history = mappings
        self.undo_btn.setEnabled(True)
        self.undo_menu_action.setEnabled(True)

        self.save_rename_log(mappings)

        self.file_list.clear()
        for file_path in self.file_paths:
            item = QListWidgetItem()
            if os.path.isdir(file_path):
                item.setText(f"📁 {os.path.basename(file_path)}")
            else:
                item.setText(f"📄 {os.path.basename(file_path)}")
            item.setToolTip(file_path)
            self.file_list.addItem(item)

        actual_renamed = sum(1 for o, n in mappings if o != n)
        error_count = len(self.current_errors)

        if error_count > 0:
            self.update_status(_("renamed_with_errors", actual_renamed, error_count))
            error_detail = "\n".join(
                f"{os.path.basename(self.file_paths[i])}: {msg}"
                for i, msg in list(self.current_errors.items())[:10]
            )
            QMessageBox.warning(self, _("dlg_complete_err"),
                                f"{_('dlg_complete')}！\n{_('success_count')}: {actual_renamed}\n{_('error_count')}: {error_count}\n\n"
                                + (f"{_('error_details')}:\n{error_detail}" if error_detail else ""))
        else:
            self.update_status(_("renamed_count", actual_renamed))

    def update_status(self, message):
        self.status_label.setText(message)


class RenamicaApp(QApplication):
    """处理 macOS 文件打开事件的 QApplication 子类"""

    def __init__(self, argv):
        super().__init__(argv)
        self._renamica_window = None
        self._pending_files = []
        self.setApplicationName("Renamica")
        self.setApplicationVersion("1.0.1")

    def set_renamica_window(self, window):
        self._renamica_window = window
        if self._pending_files:
            window.add_files_to_list(self._pending_files)
            self._pending_files = []

    def event(self, event):
        if event.type() == QEvent.FileOpen:
            file_path = event.file()
            if self._renamica_window:
                self._renamica_window.add_files_to_list([file_path])
            else:
                self._pending_files.append(file_path)
            return True
        return super().event(event)


def main():
    """主函数"""
    app = RenamicaApp(sys.argv)

    window = RenamicaGUI()
    app.set_renamica_window(window)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

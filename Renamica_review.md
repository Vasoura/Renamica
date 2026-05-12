# Renamica.py 新版检查结果

## 总体评价

新版 `Renamica.py` 相比之前有明显进步，已经从“轻量自用脚本”接近“可发布的小工具雏形”。

主要改进包括：

- 修复编号执行 bug
- 增加冲突检测
- 增加撤销功能
- 增加重命名日志
- 增加排序和手动调整
- 增加 macOS 菜单栏
- 增加 Finder FileOpen 支持

语法层面检查通过：

```bash
python3 -m py_compile Renamica.py
```

---

# 已经改好的点

## 1. 编号 bug 已修

之前执行时通过路径反查 index，容易失败。  
现在改成在循环中直接传入当前索引。

示例逻辑：

```python
new_name = self.apply_rename_rules(original_name, i)
```

并在规则函数里使用：

```python
number = self.rename_options['start_number'] + index
```

这个问题已经解决。

---

## 2. 增加了冲突检测

现在有冲突检测函数：

```python
check_rename_conflicts()
```

已检测的风险包括：

- 新文件名为空
- 非法字符
- 目标文件已存在
- 多个文件改成同名

并且有冲突时会禁用执行按钮：

```python
self.execute_btn.setEnabled(False)
```

这是很关键的安全改进。

---

## 3. 增加了撤销功能

现在已经有基础撤销函数：

```python
undo_rename()
```

执行完成后会保存映射关系：

```python
self.rename_history = mappings
```

基础撤销能力已经具备。

---

## 4. 增加了日志

现在会写入日志文件：

```text
~/.renamica/rename_log.csv
```

日志内容包括：

```csv
time,old_path,new_path,status
```

方向正确，后续可以继续补充错误信息。

---

## 5. 增加了排序和手动调整

现在已经支持：

- 按文件名排序
- 按修改时间排序
- 按创建时间排序
- 按文件大小排序
- 按文件类型排序
- 上移
- 下移

这对批量编号很重要。

---

## 6. macOS App 化相关已补充

新版已经加入：

- 菜单栏
- `File > Add Files`
- `File > Add Folder`
- `Edit > Undo Last Rename`
- `Help > GitHub`
- `RenamicaApp(QApplication)`
- `QEvent.FileOpen`

说明已经开始支持：

- macOS 菜单栏
- Finder “打开方式”
- 把文件拖到 App 图标打开

---

# 还需要修的问题

## P0：撤销后 `file_paths` 没有恢复旧路径

### 问题

现在 `undo_rename()` 成功把文件改回旧名，但最后只是刷新列表：

```python
self.refresh_file_list()
```

问题是：`self.file_paths` 里面仍然可能保存的是新路径。

例如：

```text
a.txt -> b.txt
撤销后：b.txt -> a.txt
但 self.file_paths 里仍可能是 b.txt
```

### 影响

撤销后列表可能显示异常。  
后续再次改名可能找不到文件或操作错误路径。

### 建议修复

撤销成功时同步恢复 `self.file_paths`。

示例：

```python
restored_paths = []

for old_path, new_path in self.rename_history:
    if old_path == new_path:
        restored_paths.append(old_path)
        continue

    if os.path.exists(new_path) and not os.path.exists(old_path):
        try:
            os.rename(new_path, old_path)
            restored_paths.append(old_path)
            success_count += 1
        except OSError as e:
            restored_paths.append(new_path)
            fail_count += 1
            errors.append(f"{os.path.basename(new_path)}: {e}")
    else:
        restored_paths.append(new_path)

self.file_paths = restored_paths
self.refresh_file_list()
```

---

## P0：`current_errors` 执行前没有清空

### 问题

`execute_rename()` 里没有清空：

```python
self.current_errors
```

如果上一次执行有错误，下一次成功执行后，旧错误可能仍然残留。

### 建议修复

在 `execute_rename()` 开头加入：

```python
self.current_errors = {}
```

建议位置：

```python
def execute_rename(self):
    if not self.file_paths:
        ...

    self.current_errors = {}
```

---

## P0：冲突检测按 `new_name` 判断重复，不够准确

### 问题

现在重复检测可能类似：

```python
new_name_map[new_name].append(i)
```

这会把不同文件夹下的同名文件误判为冲突。

例如：

```text
/FolderA/photo.jpg -> image.jpg
/FolderB/photo.jpg -> image.jpg
```

这两个目标路径不同，应该允许。

### 建议修复

改成按完整目标路径检测。

示例：

```python
new_path = str(Path(file_path).parent / new_name)
target_path_map[new_path].append(i)
```

这样只有目标路径完全相同才算冲突。

---

## P1：`RenameWorker` 仍然有自动 `_1`, `_2` 改名逻辑

### 问题

执行前已经有冲突检测，但 Worker 里仍然可能保留自动改名逻辑：

```python
if new_path.exists() and new_path != path_obj:
    counter = 1
    ...
    new_name = f"{name_stem}_{counter}{name_suffix}"
```

这会导致：

```text
预览显示：b.txt
实际结果：b_1.txt
```

### 建议处理

既然已经有冲突预检，建议删除 Worker 里的自动 `_1`, `_2` 改名逻辑。

原则：

```text
预览是什么，执行结果就必须是什么。
```

---

## P1：文件夹导入不是“弹窗询问”

### 当前状态

现在似乎是通过配置控制：

```python
folder_import_mode = flat / recursive
```

这也可以，但不符合之前任务里的“拖入文件夹后弹窗询问”。

### 可选方案

#### 方案 A：保留当前模式

优点：

- 不打扰用户
- 行为稳定
- 适合高级用户

建议补充：

- 在界面上显示当前导入模式
- 在设置里允许切换

#### 方案 B：拖入文件夹时弹窗询问

优点：

- 更直观
- 更适合普通用户
- 不容易误导入大量文件

建议弹窗选项：

```text
只添加当前文件夹
包含子文件夹
取消
```

---

## P1：语言配置保存可能覆盖其他配置

### 问题

切换语言时如果直接保存：

```python
save_config({LANG_KEY: self.lang})
```

会覆盖之前保存的其他配置，例如：

```python
folder_import_mode
```

### 建议修复

应基于现有配置更新：

```python
config[LANG_KEY] = self.lang
save_config(config)
```

而不是重新创建一个只包含语言字段的新配置。

---

## P1：GitHub 地址是占位地址

### 问题

当前链接类似：

```text
https://github.com/mason/Renamica
```

如果仓库还没创建，这个链接会失效。

### 建议处理

二选一：

- 改成真实 GitHub 仓库地址
- 暂时隐藏 `Help > GitHub`

---

# 当前完成度

| 模块 | 状态 |
|---|---|
| 基础 GUI | 已完成 |
| 预览 | 已完成 |
| 编号 bug | 已修 |
| 冲突检测 | 基本完成 |
| 撤销 | 有了，但需修 `file_paths` |
| 日志 | 基本完成 |
| 排序 | 已完成 |
| macOS 菜单栏 | 已完成 |
| Finder FileOpen | 已加入 |
| `.app` 打包 | 代码层面准备好了，还需 PyInstaller 配置 |
| `.icns` 图标 | 还没看到 |
| DMG / 签名 / 公证 | 未完成 |

---

# 下一步最该改的 5 件事

```md
- [ ] 修复撤销后 `self.file_paths` 不恢复的问题
- [ ] 每次执行前清空 `self.current_errors`
- [ ] 冲突检测改为按完整目标路径判断
- [ ] 删除 Worker 里的自动 `_1`, `_2` 改名逻辑
- [ ] 修复语言切换覆盖 config 的问题
```

---

# 建议优先级

## P0：必须修

- [ ] 修复撤销后 `file_paths` 不恢复的问题
- [ ] 执行前清空 `current_errors`
- [ ] 冲突检测按完整目标路径判断

## P1：重要改进

- [ ] 删除 Worker 自动 `_1`, `_2` 改名逻辑
- [ ] 修复语言配置覆盖问题
- [ ] 处理 GitHub 占位链接
- [ ] 明确文件夹导入模式

## P2：发布准备

- [ ] 增加 `.icns` 图标
- [ ] 增加 PyInstaller `.spec`
- [ ] 打包成 `Renamica.app`
- [ ] 编写 README
- [ ] 创建 GitHub Release
- [ ] 可选：打包 DMG
- [ ] 可选：Developer ID 签名
- [ ] 可选：Apple 公证 notarization

---

# 总结

新版 `Renamica.py` 已经完成了很多关键改进，特别是：

- 编号 bug 修复
- 冲突检测
- 撤销
- 日志
- 排序
- macOS 菜单栏
- Finder FileOpen

下一步重点不是继续堆功能，而是补安全一致性：

1. 撤销后路径状态一致
2. 预览和执行结果一致
3. 冲突检测按真实目标路径判断
4. 配置保存不覆盖旧配置

这些修完后，再做 `.app` 打包、图标、README 和 GitHub Release。

# Fcitx5 Theme Studio · 皮肤工坊 0.3.1

**第一次使用请阅读 [使用说明](USER_GUIDE.md)**，包括安装、图片调节、保存作品和主题恢复。本版为 Linux / Fcitx5 测试版。

![皮肤工坊界面](preview-day.png)

一个本地运行的 Linux 输入法皮肤编辑器，使用 Python 3 / PyQt6。主界面围绕配色、图片和间距组织，高级设置保留细节调节。新版采用磨砂玻璃视觉风格，支持日间和夜间模式；这是应用内渐变、半透明卡片与高光的视觉效果，不依赖桌面实时背景模糊，也不实现 Apple Liquid Glass 的动态折射。采用 MIT 许可。

## 安装

Ubuntu / Debian 及使用相同软件包体系的发行版：

```sh
sudo apt install ./fcitx5-theme-studio_0.3.1_all.deb
```

安装后在应用菜单搜索 **输入法皮肤工坊**，或运行 `fcitx5-theme-studio`。安装依赖需要联网或本机软件源。该包不替换 Fcitx5 程序、不更换默认输入法。

卸载：`sudo apt remove fcitx5-theme-studio`。卸载不删除用户设计、主题或备份；需要恢复主题时先在工坊内点击恢复。

其他 Linux 系统可安装 Python 3.10+、PyQt6 和 Fcitx5 后从源码启动：

```sh
python3 studio.py
```

例如 Ubuntu / Debian 的源码运行依赖：`sudo apt install python3-pyqt6 fcitx5 libglib2.0-bin`。

## 三步制作

1. 选择「晴空」「夜色」「纸白」配色，或修改颜色。
2. 导入图片，选择「人物靠右」「人物靠左」或「图片铺满背景」。拖动右侧画布调整位置，滚轮或「图片大小」等比缩放。推荐使用裁掉多余留白的透明 PNG。
3. 检查短、中、长预览，点击「应用到输入法」，在试打框输入拼音确认真实效果。

人物与文字重叠时，增加 **人物区域宽度**，或点击 **拉开文字与人物**。这个宽度包括人物本身和空隙，会加长真实候选框。开启独立区域后，会使用左侧或右侧锚点；仅调模拟预览宽度不会改变 Fcitx5 的候选数量。

「人物上下贴边」会去掉额外上下留白，同时保持与背景一致的 1 像素透明外沿。人物的可见轮廓也受原图留白影响。细节参数在「高级设置」中。

## 本地保存与作品库

- 关闭窗口时自动保存编辑进度，下次启动恢复图片、缩放、偏移和间距。界面日夜模式也会记住，切换模式不会更改正在设计的输入法皮肤。
- 「作品库」可填写作品名称、备注，保存当前设计，并通过缩略图列表重新打开。
- 保存设计生成 `design.json` 与 `design.assets/image.png`，图片为导入的原始像素，载入时不会丢失缩放和位移。
- 分享时将 JSON 与同名 `.assets` 文件夹一起发送，接收者点击「载入设计」即可编辑。
- 兼容之前的 version 1 JSON 设计；旧文件仍依赖原有图片路径。
- 「导出主题」生成 `theme-studio/`，内含 `theme.conf`、`background.png`、`picture.png`；安装到 `~/.local/share/fcitx5/themes/` 后在 Fcitx5 经典界面设置中选择。
- 工坊安装包与源码包不包含任何用户图片或本机配置。图片的使用、分享权限由提供者决定。

本地数据默认位于 `~/.local/share/fcitx5-theme-studio/`：`last-session.json` 和 `.assets` 保存上次编辑，`preferences.json` 保存界面模式，`library/` 保存命名作品。

右侧画布、候选预览和真实试打同时显示；通过下拉框切换短、中、长候选。预览会按可用空间缩小显示，不改变主题导出尺寸。最低窗口为 920×640；高 DPI 屏幕按 Qt 的逻辑像素布局。

在线上传、社区作者主页、公开评分、下载等功能按用户要求推迟，将来考虑接入「哼哼社」；本版没有服务器、账号或联网社区。

## 支持范围

当前只导出 **Fcitx5 经典用户界面主题**。输入引擎只要使用该界面，即可共用，例如 Fcitx5 拼音、五笔 / 码表以及 Fcitx5-Rime。桌面自带的输入法面板或应用自行绘制候选框时，可能不会采用经典界面主题。

| 环境 | 当前支持 |
| --- | --- |
| Linux + Fcitx5 经典界面 | 支持主题导出与应用 |
| Fcitx 4 / Linux 搜狗 | 未适配，请勿直接套用 |
| Windows 搜狗 | 不支持；需按搜狗格式另做导出和 Windows 测试 |
| Windows 微软拼音 / 五笔 | 不能导入 Fcitx5 主题；未发现官方支持的这类自定义图片皮肤导入接口 |
| Windows / macOS 上其他输入法 | 未适配 |

搜狗提供自己的皮肤编辑器和皮肤文件体系。Windows 11 的「个性化 → 文本输入」支持输入法主题设置，但与 Fcitx5 主题不是同一种格式，当前工坊没有适配或导入功能。

参考：[Windows 11 文本输入设置](https://learn.microsoft.com/en-us/windows/apps/develop/settings/settings-windows-11)、[Fcitx5 主题实现](https://github.com/fcitx/fcitx5/blob/5.1.19/src/ui/classic/theme.cpp)、[搜狗皮肤编辑器](https://pinyin.sogou.com/help.php?list=5&q=3)、[搜狗皮肤使用说明](https://pinyin.sogou.com/skins/skin_use.php)、[微软简体中文输入法](https://support.microsoft.com/en-us/windows/hardware/input-devices/microsoft-simplified-chinese-ime)。

## 备份与恢复

只有点击「应用到输入法」才会更改输入法主题与相关经典界面配置。每次应用前都会备份配置与原主题到：

```text
~/.local/share/fcitx5-theme-studio/backups/
```

支持 `XDG_CONFIG_HOME` 和 `XDG_DATA_HOME` 自定义路径。恢复按钮恢复最近一次应用前的状态，包括原本不存在主题的情形。重载失败会提示手动确认主题，不会自动重启输入法。程序不记录试打文字，不发送网络请求。

## 项目与开发

```text
studio.py             界面、日夜模式、会话、设计文件、应用和恢复
library_store.py      本地作品信息
theme_engine.py      图片几何、预览绘制、Fcitx5 配置导出
assets/icon.svg       图标
packaging/build.sh    Debian 安装包构建
tests/test_studio.py 功能回归检查
```

```sh
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v
sh packaging/build.sh
```

构建产物在 `dist/`。源码可以导入 Git 仓库；发布到软件仓库前需填写真实维护者信息，替换打包脚本中的占位邮箱。

## 验证与已知限制

本版在本机进行了 13 项回归检查，包括最小窗口中试打可见、大尺寸预览自适应、日夜模式不更改主题、会话恢复、本地作品库、图片缩放、区域分隔、上下边缘、设计文件、导出和应用 / 恢复；另有日夜界面截图及 Debian 包提取启动检查。安装包为可分享的本地测试版，尚未在其他机器或干净系统上安装验证。

预览不是实际候选窗口。实际高度由 Fcitx5 字体、候选词、预编辑行和 DPI 决定；图片高度按本机单行字体度量估算，跨应用或多行候选时可能需要微调。背景透明不是实时背景模糊。圆角合成模式由九宫格拉伸，图片可能变形。固定比例模式的图层不随实际候选框高度实时变化，不承诺所有 DPI 下自动贴满。

0.3.1 新增紧凑布局、居中标题、磨砂视觉、日夜模式、自动恢复和本地作品库；此前修复的 Gravity 名称、中心等比缩放与边缘对齐保留。

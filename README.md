<p align="center"><img src="assets/logo.png" width="152" alt="妄图照片直传，无文字图标"></p>
<h1 align="center">妄图照片直传</h1>
<p align="center">Wangtu Photo Transfer · Mac → USB → iPhone 系统相册</p>

把电脑中选定的照片、视频，通过数据线添加到 iPhone 的系统「照片」。支持原文件读回校验、进度回执、暂停续传与剩余空间保护。手机不需要登录 Apple 账号。

**这是开源、AI 辅助操作的开发者工具：Mac 需要 Xcode，iPhone 需要先安装本仓库的独立接收 App。没有免签安装包，也不是 App Store 上架应用。** Mac 的 Xcode 签名仍需要自己的开发团队／账号，和手机登录 iCloud 是两回事。

[交给 AI 的入口](AI-START-HERE.md) · [完整 Mac 操作](docs/MAC.md) · [Windows 状态](docs/WINDOWS.md) · [协议与恢复](docs/PROTOCOL.md) · [English](README.en.md)

## 这个工具怎么用

适合把 Mac 本机、移动硬盘或其他已挂载目录中的照片／视频，批量添加到 iPhone 相册，例如给测试手机准备素材。媒体按原文件传输，不在工具内压缩；导入后可在手机系统「照片」中查看。

工具包含 **Mac 发送脚本 + iPhone 接收 App**。目前没有 Mac 图形操作窗口，需要通过命令或让本机 AI 执行：

1. **准备接收 App**：在 Mac 用自己的 Xcode 签名环境构建，安装到你选定的 iPhone。
2. **连接和授权**：数据线连接，手机解锁、信任电脑，打开接收 App 并允许完整照片访问。
3. **先检查，再小批试传**：指定电脑素材文件夹、照片／视频范围和手机预留空间；先只生成清单，再用合成素材验证保存和视频播放。
4. **开始批量传输**：保持接收 App 在前台。程序分批保存并核验，传完或触及空间边界后停止；中断时按原工作目录续传。

AI 可以处理环境检查、构建、命令和进度核对；手机首次信任、开发者模式（系统要求时）、照片权限，以及最终照片／视频查看，需要用户亲自确认。下载仓库本身不会安装 App 或开始传输。

## 开始前需要什么

| 项目 | 要求 |
|---|---|
| Mac | 完整 Xcode，能够支持目标 iPhone 的系统版本；只有 Command Line Tools 不够 |
| Python | 3.9+，自动检查使用 3.11；当前脚本只用标准库，无需额外 pip 依赖 |
| iPhone | iOS 17+、数据线和可用空间；接收 App 运行时保持前台 |
| 签名 | Mac 上自己的有效 Xcode 开发签名环境；手机无需登录 Apple 账号 |
| 素材和工作目录 | 素材文件夹可读取；另选仓库和素材目录之外的工作目录，保存进度与临时文件 |

**Windows 用户现在无需专门连接手机测试**：目前只有离线规划，USB 传输端尚未实现。后续适配完成后，才需要 Windows + iPhone 真机验证，具体安排见 [Windows 文档](docs/WINDOWS.md)。

## 支持状态

| 能力 | 当前状态 |
|---|---|
| Mac + Xcode，USB 传入 iPhone | 已实现；基础照片／Live 引擎有真实设备读回验证 |
| 普通视频、大视频单独成批 | 已实现，自动逻辑与源码检查通过；**公开版视频真机流程待验收** |
| 指定目录、递归扫描、同名文件 | 已实现；支持仅照片／仅视频／两者 |
| Live Photo | 使用明确配对清单；不会仅凭同名猜测；由手机系统验证配对 |
| 原文件 SHA-256 读回、增量回执、空间停止 | 已实现；原始引擎已在长传输中使用 |
| Windows 目录规划和纯逻辑测试 | 已通过跨平台自动检查，见[验证矩阵](docs/VALIDATION.md)；不等于 USB 实机验证 |
| Windows 直接传 iPhone | **尚未实现**。当前发送器依赖 Xcode `devicectl` |
| iPhone App 构建／签名 | 当前需要 Mac + Xcode；不提供带作者证书的 IPA |
| Android、iPhone → 电脑、镜像遥控 | 不包含 |

公开版将原来单设备工具泛化为独立项目，去除了私人路径、设备编号和签名配置。**公开泛化版本尚未重新做整套设备验收**，请先按 Mac 文档用合成小批验证，再导入实际素材。

## 交给你的 AI

复制这一段给电脑上的 AI：

> 请接手 https://github.com/Mosigin/wangtu-photo-transfer 。先读 AI-START-HERE.md、AGENTS.md 和 docs/MAC.md。帮我把指定电脑目录里的照片／视频通过 USB 添加到我确认的 iPhone，相册现有内容保留；先确认来源、目标设备和预留空间，默认保留至少 1GB 加处理余量。遵守我对安装的授权，由我确认手机首次系统权限。先做 dry-run 和合成小批，核验保存、读回和视频播放，再持续传输。异常时用同一工作目录的账本恢复，不能清空记录或盲目重复导入。若我是 Windows，先准确说明当前只支持规划和测试，不要假称已经支持 USB。

## Mac 快速开始

完整参数、签名和人工权限步骤见 [docs/MAC.md](docs/MAC.md)。以下命令从仓库根目录运行；占位值需换成你的信息。

```sh
git clone https://github.com/Mosigin/wangtu-photo-transfer.git
cd wangtu-photo-transfer
python3 -m unittest discover -s tests -v
python3 tools/transfer.py --list-devices
```

准备独立 App 工程，默认**不编译、不安装**：

```sh
python3 tools/build.py --platform device --team YOUR_TEAM_ID \
  --bundle-id com.example.yourname.wangtu --output "$HOME/WangtuBuild"
```

取得本次安装授权后，加 `--compile --allow-provisioning-updates` 构建；用 Mac 文档中的命令安装到明确选定的设备。手机打开 App →「开始写入」→ 系统提示选择「完全访问」，保持 App 在前台。

先规划，**不会访问手机**：

```sh
python3 tools/transfer.py --source "$HOME/Pictures/ToTransfer" \
  --media all --work "$HOME/WangtuRuns/first" --reserve-gb 1
```

确认后执行（必须使用建包时同一个 Bundle ID）：

```sh
python3 tools/transfer.py --source "$HOME/Pictures/ToTransfer" \
  --media all --work "$HOME/WangtuRuns/first" --reserve-gb 1 \
  --bundle-id com.example.yourname.wangtu --device YOUR_DEVICE_ID --execute
```

- 默认保留 1GB，再加约 150MB 处理余量；电脑和手机都要有中转空间。系统其他活动可能改变容量，不能保证精确停在某个字节。
- 大于常规批次的视频可以单独处理；如果没有任何剩余项目能安全容纳，会停止并报告 `no_item_fits_safe_budget`，不会为填满空间生成副本。
- 目录扫描支持 JPEG、HEIC/HEIF、PNG、GIF、BMP、TIFF、DNG，以及 MOV、MP4、M4V。扩展名可识别不代表任何编码都被手机支持；不兼容会保留原文件并记录失败。
- 图片和 MOV 同名时，默认是两个独立媒体。需要保留 Live 的，请提供[显式配对清单](docs/MAC.md#live-photo与拍摄日期)。
- 原文件嵌入的 EXIF 等不会被本工具转码或改写；系统相册时间线需要精确拍摄时间时，请在清单中填写 `creationDate`。

## 暂停和恢复

在工作目录创建 `STOP` 文件，或在手机点「暂停」。重启前删除电脑工作目录的 `STOP`，手机点「开始写入」，然后执行**相同命令和同一工作目录**。

工作目录保存 `plan.json`、`ledger.json`、`progress.json`、`summary.json` 和少量暂存。不要删除、分享或提交这些私人文件。进程异常退出不代表这一批没有保存；先核对回执再恢复。[恢复说明](docs/PROTOCOL.md)

正常结束看 `summary.json`：`verified` 是已核验数量，`failed` 是失败数量，`remaining` 是未处理数量，`freeBytes` 是手机当时的实际剩余空间。只有失败、未处理和未知项都已核对，才能判断是否全部完成；空间不足停止不等于传完。

## 常见使用问题

- **会清空手机相册吗？** 只添加选定媒体，不删除或替换手机已有内容。
- **会自动识别手机里已有的相同照片吗？** 不做全库查重；续传依靠本工具的保存记录，不能用删除记录或重装 App 的办法重试。
- **文件夹会变成手机相簿吗？** 目前只导入媒体，不恢复文件夹／相簿结构、收藏、隐藏或编辑历史。
- **能只传照片、保留视频吗？** 使用 `--media photos`；手机已有视频保持原状。只传视频用 `--media videos`。
- **Live 和拍摄时间怎么保留？** Live 使用显式配对清单；需要精确设置相册时间线时填写带时区的拍摄时间，见 [Mac 文档](docs/MAC.md#live-photo与拍摄日期)。
- **断线或报错后怎么办？** 保留原素材、工作目录和接收 App 的记录，按[恢复说明](docs/PROTOCOL.md)核对后继续；不要直接开一个空任务重发全部素材。

## 数据边界

- 只添加用户选定的媒体，不删除、替换或整理系统相册现有资产。
- 不改动电脑源文件，不使用硬链接交给系统移动原件。
- App 没有自建网络上传功能；**若用户已启用系统 iCloud 照片，系统仍可能同步新存入的媒体**。本工具不会替你更改 iCloud 设置。
- 完整照片权限用于按本工具持久化的资产 ID 核验保存结果，不扫描已有图库内容。
- 不把证书、描述文件、设备信息、私人素材和传输记录上传到本仓库。

## 许可证和图标

代码与随库图标采用 [MIT](LICENSE)。无文字图标由内置图像生成工具制作，生成说明与提示词见 [assets/LOGO.md](assets/LOGO.md)。

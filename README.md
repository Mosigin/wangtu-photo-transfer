<p align="center"><img src="assets/logo.png" width="152" alt="妄图照片直传，无文字图标"></p>
<h1 align="center">妄图照片直传</h1>
<p align="center">Wangtu Photo Transfer · Mac → USB → iPhone 系统相册</p>

把电脑中选定的照片、视频，通过数据线添加到 iPhone 的系统「照片」。支持原文件读回校验、进度回执、暂停续传与剩余空间保护。手机不需要登录 Apple 账号。

**这是开源、AI 辅助操作的开发者工具：Mac 需要 Xcode，iPhone 需要先安装本仓库的独立接收 App。没有免签安装包，也不是 App Store 上架应用。** Mac 的 Xcode 签名仍需要自己的开发团队／账号，和手机登录 iCloud 是两回事。

[交给 AI 的入口](AI-START-HERE.md) · [完整 Mac 操作](docs/MAC.md) · [Windows 状态](docs/WINDOWS.md) · [协议与恢复](docs/PROTOCOL.md) · [English](README.en.md)

## 支持状态

| 能力 | 当前状态 |
|---|---|
| Mac + Xcode，USB 传入 iPhone | 已实现；基础照片／Live 引擎有真实设备读回验证 |
| 普通视频、大视频单独成批 | 已实现，自动逻辑与源码检查通过；**公开版视频真机流程待验收** |
| 指定目录、递归扫描、同名文件 | 已实现；支持仅照片／仅视频／两者 |
| Live Photo | 使用明确配对清单；不会仅凭同名猜测；由手机系统验证配对 |
| 原文件 SHA-256 读回、增量回执、空间停止 | 已实现；原始引擎已在长传输中使用 |
| Windows 目录规划和纯逻辑测试 | 代码可移植，配置了 Windows CI；不等于 USB 实机验证 |
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

## 数据边界

- 只添加用户选定的媒体，不删除、替换或整理系统相册现有资产。
- 不改动电脑源文件，不使用硬链接交给系统移动原件。
- App 没有自建网络上传功能；**若用户已启用系统 iCloud 照片，系统仍可能同步新存入的媒体**。本工具不会替你更改 iCloud 设置。
- 完整照片权限用于按本工具持久化的资产 ID 核验保存结果，不扫描已有图库内容。
- 不把证书、描述文件、设备信息、私人素材和传输记录上传到本仓库。

## 许可证和图标

代码与随库图标采用 [MIT](LICENSE)。无文字图标由内置图像生成工具制作，生成说明与提示词见 [assets/LOGO.md](assets/LOGO.md)。

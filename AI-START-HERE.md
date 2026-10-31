# AI 接手入口

这是「妄图照片直传 / Wangtu Photo Transfer」，一个独立仓库。

先读 `AGENTS.md`、`README.md`、`docs/MAC.md`。Windows 请求还要读 `docs/WINDOWS.md`。

## 你要完成什么

帮助用户将明确目录内的照片／视频，经 USB 添加到用户选定的 iPhone。已存在的相册媒体保持原状。采用独立 App + Apple PhotoKit，桌面端用 Xcode 自带 devicectl；不要求用户登录手机 Apple 账号，不使用 Finder 照片同步。

## 建议操作顺序

1. 只读核对环境：Mac、Xcode、Python 3.9+、手机连接；明确用户选择的目标、素材范围、预留空间。
2. 跑 `python3 -m unittest discover -s tests -v`，看当前验证矩阵；不要把规划／类型检查当成设备传输成功。
3. 用 `tools/transfer.py --list-devices` 找实际设备 ID，不能使用仓库或其他电脑的旧编号。用户已指明且只有一个匹配目标时直接核对，不重复问。
4. 用自己的 Bundle ID 和已有合法签名环境生成工程。只有具备用户当前安装授权，才执行编译和安装。默认 `build.py` 只准备临时工程。
5. 用户在手机打开 App、点「开始写入」并确认完整照片权限。不要让用户发密码、证书或 Apple 凭据。
6. 先生成合成小批，执行 dry-run；实际写入后核验手机回执与原资源读回，并让用户核对视频播放。见 Mac 文档的 smoke 章节。
7. 用 `--source`、`--media`、明确 `--device`、同一 `--bundle-id`、仓库外 `--work` 与 `--reserve-gb` 持续执行。
8. 观察 `progress.json` 和日志。失败时先看 `ledger.json` 的 pending 与手机状态，照协议恢复，不盲目重发。源文件／工作目录移动会改变指纹，需要先核对。
9. 结束必须读取 `summary.json`，核对 verified、failed、remaining、freeBytes 和停止原因。源素材未传完而空间不足时要明确说出。保留私有账本，停止本次防休眠，告诉用户实际结果。

## 不可省略的事实

- 当前只有 Mac 的 USB 后端；Windows 只可规划和运行纯逻辑测试。
- 普通视频与公开泛化版尚未完成新的真机验收；使用前做小批。基础照片／Live 引擎的既往验证不能证明所有编码和所有设备支持。
- Live 必须来自显式清单并通过手机系统验证；不要凭同名把普通视频当动态配套。
- Apple 签名在 Mac 上完成；没有作者通用证书或“免签 IPA”。用户可能需要在 Xcode 登录自己的开发账号，免费团队的限制由 Apple 决定，不保证永久免费／永久有效。
- 暂存、Photos 系统元数据、缩略图都消耗空间；源媒体字节不等于手机实际占用变化。

## 代码地图

- `tools/media_plan.py`：跨平台离线目录／清单规划、同名隔离、空间与批次规则。
- `tools/transfer.py`：Mac USB 发送、回执、恢复、原文件摘要、停止。
- `tools/build.py`：在指定输出目录生成独立 Xcode 工程，提取中英文资源，打入 AppIcon。
- `ios/ImportPolicy.swift`：schema、资源组合、路径和保留空间边界。
- `ios/WangtuPhotoTransfer.swift`：手机 UI、PhotoKit 保存与读回、增量日志、空间停止。
- `ios/*.xcstrings`：唯一的界面／权限翻译来源。
- `tests/`、`.github/workflows/checks.yml`：规划／协议测试与 Mac 源码检查。

需要扩展 Windows 时，不要用文件复制冒充写入系统相册：仍需同一已签名 iOS App，在相册 API 中执行保存与核验。先增加独立 Transport 后端，再在 Windows + 驱动 + 实际 iPhone 上测完整闭环。

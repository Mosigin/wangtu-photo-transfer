# Windows：当前范围和后续适配

**当前 Windows 不能直接传入 iPhone。** `--execute` 会明确拒绝，避免把规划结果冒充传输成功。

## 现在需要用户测试吗？

**暂时无需为此专门连接手机测试。** 先要开发 Windows USB 传输端；仅运行当前脚本无法验证尚未实现的传输功能。已有 Windows 自动检查验证了规划与协议逻辑，见[验证记录](VALIDATION.md)。

如果只是提前检查自己的目录能否被正确识别，可选做下面的离线规划，无需手机或 Apple 驱动。结果只证明电脑端能读出候选清单，不证明媒体已进入手机。

## 可选：在 Windows 做离线规划

先下载本仓库并在项目根目录打开 PowerShell；安装 Python 3.9+（CI 使用3.11）。以下示例的 `D:\Media` 换成你自己的素材文件夹，工作目录保持在素材和仓库之外。

现在可以在 Windows 使用 Python 3.9+ 做目录／显式清单规划，并运行纯逻辑测试：

```powershell
py -3 -m unittest discover -s tests -v
py -3 tools/transfer.py --source "D:\Media" --work "$env:USERPROFILE\WangtuRuns\plan" --media all
```

这不会连接手机。CI 配置包含 Windows 的规划和协议测试；即使 CI 全绿，也不代表 Windows 的驱动、签名、USB 和 Photos 保存已验证。

输出应显示 `execute=false`、所选媒体数量与源文件大小；私人工作目录内有 `plan.json`。中文目录、空格文件名、不同子目录同名文件都可以作为检查用例。不要在 Windows 执行 Mac 文档中的 `xcrun`、`devicectl` 或 `--compile` 命令。

## 为什么还不能直接支持

桌面后端目前调用 Xcode 自带 `devicectl`；它是 Mac 工具。iPhone 接收 App 仍然要由合法环境构建／签名并安装，不能把电脑文件拷到某个目录就当作进入系统相册。

## 可行的后续方向

[`pymobiledevice3` 官方项目](https://github.com/doronz88/pymobiledevice3)提供 Windows／Linux／macOS 的设备通信能力及应用容器访问。可以在相同协议之下增加可选 Windows Transport 后端；本仓库尚未包含或验证它，不自动安装依赖。

仍需要一台 Mac／合法构建环境先给目标手机制作可运行的独立 App。[Apple 的构建运行说明](https://help.apple.com/xcode/mac/current/en.lproj/devdc0193470.html)可作为环境入口。Windows 驱动应按所用设备库的[官方排障文档](https://doronz88.github.io/pymobiledevice3/guides/troubleshooting/)核对，不能认为“安装任意 iTunes／Apple Devices 版本”一定兼容。

## 什么时候需要 Windows 真机测试

先完成 Windows 传输后端、设备识别、应用容器读写以及沿用现有回执的恢复流程，再安排用户实测。只有一台 Windows 电脑还不能完成当前 iOS App 的构建签名；测试前先在 Mac 上为该测试手机准备可运行的接收 App。

届时准备：Windows 电脑、已获授权的测试 iPhone、数据线，以及几张合成照片和一段短视频；手机保留足够空闲空间。记录实际系统／驱动版本即可，不需要公开账号或设备编号。

| 测试 | 应观察到的结果 |
|---|---|
| 小批照片与视频 | 系统照片里能看到，视频能播放，原资源读回核验通过 |
| 暂停与恢复 | 使用同一账本继续，数量与回执一致 |
| 受控断线重连 | 先核对上一批结果，无盲目重传或重复资产 |
| 接近设定预留空间 | 自动停止，准确报告已传／未传数量和实际余量 |
| 可选 Live／大视频 | 单独记录格式与大小、成功／失败／未知结果 |

普通使用验证从合成小批开始；断线／空间等专项在后端完成且已有恢复方案后进行，不要求用户现在自行制造故障。

## 给后续 Windows AI 的验收清单

1. 记录 Windows、Python、Apple 驱动／服务、设备通信库和手机系统版本；不公开设备ID。
2. 用户完成 USB 信任，识别正确的物理设备；不降低安全设置或借用别人的签名。
3. 证明能够读写**本接收 App**的私有容器，复用现有 schema 和身份／摘要校验，不直接改 Photos 数据库／DCIM。
4. 先发合成 JPEG／PNG／HEIC、视频和明确有效的 Live 配对，核对保存、原资源读回与用户播放。
5. 覆盖同名跨目录、大视频、断线、半文件、未知提交恢复、授权变化和低空间停止；确认无重复资产、无原片误删。
6. 自动逻辑／驱动成功／App安装／Photos保存／播放验收分别记账。完成真实闭环之后，才修改 README 的 Windows USB 状态。

无需为了尝试 Windows 改 iPhone Apple 账号或打开 iCloud；也不需要重新导入原有全部媒体。

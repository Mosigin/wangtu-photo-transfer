# Windows：当前范围和后续适配

**当前 Windows 不能直接传入 iPhone。** `--execute` 会明确拒绝，避免把规划结果冒充传输成功。

现在可以在 Windows 使用 Python 3.9+ 做目录／显式清单规划，并运行纯逻辑测试：

```powershell
py -3 -m unittest discover -s tests -v
py -3 tools/transfer.py --source "D:\Media" --work "$env:USERPROFILE\WangtuRuns\plan" --media all
```

这不会连接手机。CI 配置包含 Windows 的规划和协议测试；即使 CI 全绿，也不代表 Windows 的驱动、签名、USB 和 Photos 保存已验证。

## 为什么还不能直接支持

桌面后端目前调用 Xcode 自带 `devicectl`；它是 Mac 工具。iPhone 接收 App 仍然要由合法环境构建／签名并安装，不能把电脑文件拷到某个目录就当作进入系统相册。

## 可行的后续方向

[`pymobiledevice3` 官方项目](https://github.com/doronz88/pymobiledevice3)提供 Windows／Linux／macOS 的设备通信能力及应用容器访问。可以在相同协议之下增加可选 Windows Transport 后端；本仓库尚未包含或验证它，不自动安装依赖。

仍需要一台 Mac／合法构建环境先给目标手机制作可运行的独立 App。[Apple 的构建运行说明](https://help.apple.com/xcode/mac/current/en.lproj/devdc0193470.html)可作为环境入口。Windows 驱动应按所用设备库的[官方排障文档](https://doronz88.github.io/pymobiledevice3/guides/troubleshooting/)核对，不能认为“安装任意 iTunes／Apple Devices 版本”一定兼容。

## 给后续 Windows AI 的验收清单

1. 记录 Windows、Python、Apple 驱动／服务、设备通信库和手机系统版本；不公开设备ID。
2. 用户完成 USB 信任，识别正确的物理设备；不降低安全设置或借用别人的签名。
3. 证明能够读写**本接收 App**的私有容器，复用现有 schema 和身份／摘要校验，不直接改 Photos 数据库／DCIM。
4. 先发合成 JPEG／PNG／HEIC、视频和明确有效的 Live 配对，核对保存、原资源读回与用户播放。
5. 覆盖同名跨目录、大视频、断线、半文件、未知提交恢复、授权变化和低空间停止；确认无重复资产、无原片误删。
6. 自动逻辑／驱动成功／App安装／Photos保存／播放验收分别记账。完成真实闭环之后，才修改 README 的 Windows USB 状态。

无需为了尝试 Windows 改 iPhone Apple 账号或打开 iCloud；也不需要重新导入原有全部媒体。

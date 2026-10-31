# Mac 使用与 AI 操作流程

从仓库根目录运行。需要 Python 3.9+、完整 Xcode（仅 Command Line Tools 不够）、USB 数据线和受该 Xcode 支持的 iPhone。本 App 最低 iOS 17；实际设备系统是否兼容当前 Xcode，先用 `devicectl` 核对。解锁手机并信任电脑；若签名运行要求开发者模式，用户在手机设置中启用并完成系统步骤。

## 1. 环境和目标

```sh
xcode-select -p
xcrun devicectl list devices
python3 --version
python3 -m unittest discover -s tests -v
```

若有多台手机，明确目标；后续每条命令的 `YOUR_DEVICE_ID` 必须是这台物理设备。不要选择模拟器、其他人的手机或只有无线连接的设备。

## 2. 准备、编译和安装

独立 Bundle ID 示例 `com.example.yourname.wangtu`。请选你自己的唯一标识，建包和发送必须一致。`YOUR_TEAM_ID` 在 Xcode 的 Signing & Capabilities 中核对；不要把它写死提交到公开库。

仅准备工程，不编译：

```sh
python3 tools/build.py --platform device --team YOUR_TEAM_ID \
  --bundle-id com.example.yourname.wangtu --build 1 --output "$HOME/WangtuBuild"
```

得到用户本次安装授权后，编译：

```sh
python3 tools/build.py --platform device --team YOUR_TEAM_ID \
  --bundle-id com.example.yourname.wangtu --build 1 --output "$HOME/WangtuBuild" \
  --compile --allow-provisioning-updates
```

如果签名失败，在 Xcode 中打开**生成的**工程核对自己的账号与团队，按 Apple 提示完成，不借用作者证书。不要对这个用户的其他 App 执行重置或卸载。

```sh
codesign --verify --deep --strict "$HOME/WangtuBuild/DerivedData/Build/Products/Debug-iphoneos/WangtuPhotoTransfer.app"
xcrun devicectl device install app --device YOUR_DEVICE_ID \
  "$HOME/WangtuBuild/DerivedData/Build/Products/Debug-iphoneos/WangtuPhotoTransfer.app"
xcrun devicectl device info apps --device YOUR_DEVICE_ID --bundle-id com.example.yourname.wangtu
xcrun devicectl device process launch --device YOUR_DEVICE_ID com.example.yourname.wangtu
```

手机打开「妄图照片直传」，点「开始写入」，用户确认系统完整照片访问。运行期间保持 App 前台、数据线连接。开始状态会暂时防止手机自动锁屏，暂停／空间停止后恢复。

## 3. Smoke：先用合成小批验证

工具可生成纯程序合成 PNG／JPEG／HEIC 和一秒 MOV（不是私人素材）：

```sh
xcrun swiftc -parse-as-library tools/MakeSmokeMedia.swift -o /tmp/wangtu-make-smoke
/tmp/wangtu-make-smoke "$HOME/WangtuSmokeMedia"
python3 tools/transfer.py --source "$HOME/WangtuSmokeMedia" --work "$HOME/WangtuRuns/smoke"
```

确认 dry-run 范围与空间，再加 `--device YOUR_DEVICE_ID --bundle-id com.example.yourname.wangtu --execute`。需要同时验证：

1. 主机 `summary.json`：全部为 verified，failed 为0，没有 pending。
2. 手机系统照片中有新增素材，视频可以播放。
3. 每个资源是本机 readback SHA-256 核验后的结果，不能把“拷入 App 容器”当相册保存。
4. 暂停、同一工作目录恢复，不应创建新的副本。
5. Live 是额外用例，用下节明确配对清单，确认系统显示 LIVE 并能播放。

本仓库公开版视频原生闭环尚待实机验收；如果你完成了，请在自己的设备记录系统版本、工具版本、编码、结果，不公开设备编号或私人文件。

## 4. 实际目录传输

```sh
python3 tools/transfer.py --source "/path/to/your/media" --media all \
  --work "$HOME/WangtuRuns/my-transfer" --reserve-gb 1
```

`--media photos` 只选照片，`videos` 只选视频，`all` 选两者；默认 all。确认后增加以下三个参数：

```sh
--device YOUR_DEVICE_ID --bundle-id com.example.yourname.wangtu --execute
```

大视频默认单独成批，仍受手机双份临时空间预算与电脑中转空间预算保护。可用 `--timeout 1800` 调整单次设备命令超时（10～3600秒）。默认每常规批最多20项、约32MB。

建议长传输用临时防休眠断言包住同一命令，进程结束自动恢复：

```sh
caffeinate -i python3 tools/transfer.py --source "/path/to/your/media" \
  --work "$HOME/WangtuRuns/my-transfer" --reserve-gb 1 \
  --device YOUR_DEVICE_ID --bundle-id com.example.yourname.wangtu --execute
```

## Live Photo与拍摄日期

扫描目录不会凭同名猜测 Live。需要时在私人工作区建立显式 JSON 清单：

```json
{
  "schema": 1,
  "entries": [
    {"photo": "photos/IMG_1001.HEIC", "pairedVideo": "photos/IMG_1001.MOV", "creationDate": "2024-05-01T12:00:00+08:00"},
    {"photo": "photos/ordinary.jpg"},
    {"video": "videos/clip.mp4", "creationDate": "2024-05-02T14:00:00+08:00"}
  ]
}
```

路径相对于 `--source`，不能越界或重复。`creationDate` 可省略；精确时间需要带时区。原文件 EXIF 字节仍完整保留，但不提供时间时，不能承诺系统照片时间线一定按原拍摄时间排列。清单不搬运用户相簿、收藏、隐藏和非破坏编辑关系。

传入参数 `--manifest "/private/path/manifest.json"`。Live 组合先由 iPhone 的 `PHLivePhoto` 接口验证；不正确会停下，不会自动转成两个资产冒充成功。

## 5. 暂停、恢复、结束

```sh
touch "$HOME/WangtuRuns/my-transfer/STOP"
```

或在手机点「暂停」。当前一个小事务可能继续至安全边界。保留原 `--work`；恢复时删除电脑 STOP 文件，手机重新点「开始写入」，再执行同一命令。不要删除 `ledger.json` 或手机 `receipts.jsonl`。

停止原因见 `summary.json`：

- `source_exhausted`：所选素材都已处理；还要看 failed。
- `reserve_reached`：手机余量保护触发，remaining 通常不为0。
- `no_item_fits_safe_budget`：剩余项目中没有能安全放下的；例如仅剩超大视频，手机可能还剩多于预留值的空间。

正常结束应没有未知 pending。异常退出则按[协议文档](PROTOCOL.md)先核对手机状态，禁止假称完成。实际余量可能因系统活动变化。

## 常见问题

- **找不到 devicectl**：需要完整 Xcode，并确认 `xcode-select` 指向它。
- **权限未完全允许**：用户在手机系统设置中检查该 App 的照片权限；不要由 AI 擅自扩大授权。
- **status 过期**：保持 App 前台、解锁并连接数据线；修复后用同一工作目录恢复。
- **USB 读状态瞬断**：程序最多只读重试6次；仍失败则停下，不会因没读到回执就重建资产。
- **不兼容视频／DNG／图片**：扩展名只是初筛，手机系统支持由编码和资源决定；源文件保留，核对失败记录。
- **App 容器路径复制失败**：确认所装为自己签名、允许开发容器访问的开发包，Bundle ID 一致。不要绕过系统保护去写 DCIM。

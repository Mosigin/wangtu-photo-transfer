# USB 协议、状态和恢复

版本：`schema = 1`。这是专用 App 容器协议，不是 Photos 私有数据库协议。

## 桌面 → 手机

1. 规划器在指定根目录内选择媒体，生成稳定来源 ID。不同子目录的同名文件有不同 ID 与暂存文件名；`originalFilename`保留原文件名。
2. 主机在私有工作目录将本批存为 `ledger.pending` 并原子保存。每个原资源计算 SHA-256，再复制到独立暂存并核对摘要。
3. 观察连接为 wired，复制本批到 `Documents/Incoming/<batch-id>/`。所有资源复制完成后，最后发送 `Documents/request.json`。
4. 手机校验schema、资源组合、路径、原文件名、大小与摘要。目录名／文件名不允许越界和符号链接。资源只能是一个photo、一个video，或photo+pairedVideo。
5. Live 先通过系统 `PHLivePhoto` 验证。当前实际可用空间必须继续满足 `reserveBytes + 150MB`；批次规划还事先预留双份复制空间。

请求示意（真实的大小／摘要必须从源文件产生，禁止照抄示例值）：

```json
{"schema":1,"id":"usb-PLANHASH-000001","reserveBytes":1000000000,"entries":[
  {"id":"wt-STABLESOURCEID","creationDate":null,"resources":[
    {"file":"STABLESOURCEID-video.mov","originalFilename":"clip.mov","kind":"video","bytes":123,"sha256":"ACTUAL_64_LOWERCASE_HEX_DIGITS"}
  ]}
]}
```

## 手机事务与回执

- 创建 asset request 后，**在 PhotoKit 提交前**把占位资产ID和本项完整清单追加到 `Documents/receipts.jsonl` 并同步到存储。失败时拒绝提交，不能吞写入错误继续。
- 资源的 `shouldMoveFile=true` 只作用于独立 App 内经复制、核对过的暂存文件，不作用于电脑原文件或用户相册原件。
- PhotoKit 返回后，通过该资产ID获取新资源；禁止网络下载。逐块读取并校验 SHA-256、原资源大小、媒体类型、资源名以及Live标记。
- 通过后追加 `verified` 回执，再清理本工具剩余暂存。明确失败与未知提交分别处理，未知不自动重建。
- `status.json` 原子更新，含 `batch`、本批 `results`、`state`、`freeBytes`、`imported`、`failed`、`authorized`、`enabled` 与时间。主机读状态瞬断最多6次只读重试。

## 空间停止

在下一项保存前触及余量时，手机先持久保存 `space-stop.json`，清理本批未提交暂存，返回部分成功结果，设置 `state=space, enabled=false`。后续空闲 tick 以及重开保持此状态。

主机将本批已经verified／failed的结果收到账本；未开始的不算失败、不算成功，pending结束后仍保留为可选来源。显式继续后，手机等待一个新的批次ID，不再读取已清理的旧批资源。

默认预留1GB，并另留150MB元数据处理余量。Photos 缩略图、文件系统和其他 App 会改变实际容量，所以最终不能简单用源文件字节相减，也不能保证精确停在整数GB。

## 断线与未知提交

- 复制资源时断线：`request.json` 尚未送达则不应开始保存；重连后先读手机状态，再从同一主机pending恢复。
- 请求已到、主机未收到回执：不要直接重新发送；若手机batch匹配，就等待／读取它的结果。完成后只合并已有结果。
- 手机在保存后、写verified前退出：以pending持久化的资产ID读回核验。查不到或资源不符时停止，让人检查，不创建“可能重复”的新资产。
- 手动暂停：主机或手机的STOP只作用于本工具，当前单个事务可能先到安全边界。恢复保留同一来源和账本。
- 日志损坏／无换行的半条日志：停止，不把它当空历史，不自动删除修复。
- `failed` 默认不再自动重发。同一source ID若内容／清单变化，手机会阻断；修复格式应产生明确的新来源，而不能伪装成原来的已核验文件。

## 边界

- 这不是密码学可信设备证明；主机与用户授信的接收App共享信任边界。
- 增量日志校验并非 Photos 全库备份；只核对本工具本次新资产，不证明用户已有图库全部完整。
- 文件导入保留原始资源字节，不自动恢复相簿关系、收藏／隐藏状态、编辑历史或完整连拍分组。
- Windows 后端仍未实现；扩展时必须保持相同的先持久意图、未知提交核对和空间保护规则。

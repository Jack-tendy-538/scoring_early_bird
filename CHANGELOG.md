# CHANGELOG

All notable changes to this project will be documented in this file.

## v1.0.0-beta.3 - 2025-10-09 (Pre-release)

本次为预发布测试版，适用于学生登记考勤情况的工具。建议将此版本标记为 Pre-release。

亮点
- 改进 CSV 导入/导出与时间解析（支持更多时间格式）。
- 增强输入校验与错误日志，减少因数据异常导致的崩溃。
- 优化批量导入性能，降低大文件处理时的内存占用。
- 更新 CLI 与示例配置，便于部署与自动化使用。

详细变更

新增（New）
- 新增 CSV 批量导入命令，支持多种时间格式解析与容错处理。
- 新增按班级/日期生成汇总报告的 CLI 子命令。
- 添加示例配置文件 config.sample.yaml，便于自定义计分与解析规则。

改进（Changed / Improved）
- 导入逻辑：加强字段校验并提供友好报错提示。
- 性能：优化大文件处理，降低峰值内存占用和 IO 瓶颈。
- 日志：增加日志等级与错误追踪信息，便于排查问题。

修复（Fixed）
- 修复当某些行缺失时间字段时程序崩溃的问题（改为跳过并记录警告）。
- 修复导出时部分时区信息丢失的问题（保留原始时间字符串作为备用字段）。

破坏性变更（Breaking Changes）
- 无重大破坏性变更。本次为 beta 小版本；若未来更改配置格式，将在发布说明中提供迁移步骤。

升级/迁移说明
- 升级前请备份现有数据与配置文件。
- 若使用自定义配置，请参考 config.sample.yaml 校验字段兼容性。
- 安装（开发环境示例）：
  git clone https://github.com/Jack-tendy-538/scoring_early_bird.git
  cd scoring_early_bird
  pip install -e .

已知问题
- 少数非常规时间格式可能仍需在配置中手动指定解析格式。
- 若项目包含 Web/GUI，部分视图在小屏幕设备上显示布局尚需优化。

贡献者
- @Jack-tendy-538（维护者）
- 其它贡献者：如有请补充具体用户名。

附：供 Releases 页面粘贴的发布草稿（可直接复制）

Title: v1.0.0-beta.3 — 测试版（学生考勤登记）

This is a beta release for the student attendance registration tool.

Highlights
- Improved CSV import/export and time parsing.
- Better input validation and error logging.
- Performance improvements for bulk imports.
- Updated CLI and example configuration.

Changelog
(New)
- Add CSV bulk import command.
- Add reporting by class/date.

(Changed)
- Improved validation and logging.

(Fixed)
- Prevent crash on missing time fields.
- Preserve timezone in exports.

Known issues
- Nonstandard time formats may require manual config.

Upgrade notes
- Backup data and config before upgrading.
- See config.sample.yaml for config changes.

Contributors
- @Jack-tendy-538
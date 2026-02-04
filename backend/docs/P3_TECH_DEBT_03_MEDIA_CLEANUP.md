# P3 技术债 TD-03：media 用户数据清算

- `backend/media/` 为用户上传及运行时生成的数据，不纳入版本控制。
- 由部署挂载或对象存储（volume / S3 / OSS）提供；生产环境需在部署阶段配置 `MEDIA_ROOT` 及存储方式。

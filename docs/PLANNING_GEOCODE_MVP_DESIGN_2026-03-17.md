# 规划点位批量导入与自动定位矫正系统设计（MVP）

**文档版本**: v1.1  
**更新日期**: 2026-03-17  
**适用路径前缀**: `/charging/admin/api`

---

## 1. 文档目标

本文档用于将“规划专题点位可视化”需求转化为可直接执行的接口与业务规范，重点补齐以下内容：

1. 每个核心接口的请求/响应示例  
2. 状态机硬规则（禁止流转）  
3. 发布策略定版（覆盖与冲突）  
4. 地理编码主备服务参数  
5. 县域边界校验口径  
6. 测试与验收阈值基线  

---

## 2. 核心业务对象

1. `planning_topics`：规划专题  
2. `planning_versions`：专题版本  
3. `geocode_batches`：导入批次  
4. `staging_points`：待定位点位池  
5. `geocode_attempts`：定位尝试日志  
6. `geocode_candidates`：候选坐标  
7. `address_corrections`：地址修正词典  
8. `publish_logs`：发布记录  

---

## 3. 状态机硬规则（定版）

### 3.1 `staging_points.geocode_status`

允许状态：

1. `pending`
2. `geocoding`
3. `auto_pass`
4. `need_review`
5. `manual_confirmed`
6. `failed`
7. `published`

允许流转：

1. `pending -> geocoding`
2. `geocoding -> auto_pass`
3. `geocoding -> need_review`
4. `geocoding -> failed`
5. `need_review -> manual_confirmed`
6. `failed -> geocoding`
7. `auto_pass -> published`
8. `manual_confirmed -> published`

禁止流转（硬规则）：

1. `published -> *`（禁止重试、禁止改坐标、禁止改状态）  
2. `auto_pass -> geocoding`（必须通过“回退为 need_review”专用管理操作，默认关闭）  
3. `manual_confirmed -> geocoding`（同上）  
4. `failed -> published`（必须先变为 `auto_pass` 或 `manual_confirmed`）  

### 3.2 `planning_versions.stage`

允许状态：

1. `draft`
2. `review`
3. `locked`
4. `archived`

硬规则：

1. `locked` 版本禁止导入、重试、矫正、发布覆盖  
2. `locked` 默认不允许解锁；如需解锁，必须管理员执行“解锁审批流程”（MVP 默认不提供 UI，只保留后台运维开关）  
3. `archived` 只读  

---

## 4. 发布策略定版

发布接口：`POST /geocode/batches/{batch_id}/publish`

### 4.1 覆盖策略 `overwrite_policy`

1. `no_overwrite`（默认）：同版本已有同名近邻点时跳过  
2. `same_name_overwrite`：同名点覆盖（同专题同版本）  
3. `near_merge`：在阈值半径内按近邻合并（保留最新）  

### 4.2 冲突判定（MVP）

1. 主键冲突：`topic_id + version_id + point_name + normalized_address`  
2. 空间冲突：同专题同版本内，点间距离 `< 50m` 视为近邻冲突  
3. 冲突处理记录入 `publish_logs` 的 `skipped_reason`  

### 4.3 发布前硬校验

1. 仅允许 `auto_pass` 与 `manual_confirmed` 进入发布集  
2. `need_review` 与 `failed` 必须为 0（除非传入显式跳过参数，默认不允许）  
3. 坐标必须通过边界校验  
4. 版本必须不是 `locked` 之外的非法状态  

---

## 5. 地理编码服务参数（主备定版）

### 5.1 服务配置

1. 主服务：`provider_primary`（例如高德）  
2. 备服务：`provider_secondary`（例如天地图或自建服务）  

### 5.2 运行参数（默认值）

1. `request_timeout_ms = 5000`
2. `max_retries_per_point = 3`
3. `retry_backoff_ms = [500, 1000, 2000]`
4. `candidate_topn = 3`
5. `batch_concurrency = 10`
6. `qps_limit_primary = 20`
7. `qps_limit_secondary = 10`

### 5.3 分流阈值

1. `score >= 0.85` -> `auto_pass`
2. `0.60 <= score < 0.85` -> `need_review`
3. `score < 0.60` -> `failed`

### 5.4 供应商异常处理

1. 主服务超时/5xx：立即切备服务  
2. 备服务也失败：记录 `last_error` 并置 `failed`  
3. 每次尝试必须写入 `geocode_attempts`  

---

## 6. 边界校验口径（多县专题）

### 6.1 判定逻辑（统一）

1. 优先使用点位的 `county` 字段对应的县域多边形  
2. 若 `county` 为空，使用 `topic.county_scope` 的默认县域  
3. 多县专题必须先确定“归属县”，再做 `Point in Polygon` 校验  

### 6.2 坐标归属规则

1. 点落在唯一县域内：通过  
2. 点落在多个县域边界重叠区：标记 `need_review`（不可自动通过）  
3. 点落在所有县域外：标记 `failed`（不可发布）  

### 6.3 人工修正规则

1. 手工点选必须再次跑边界校验  
2. 不通过时接口直接拒绝并返回“边界外”  

---

## 7. 接口字段级样例（核心接口）

统一响应：

```json
{
  "success": true,
  "data": {},
  "error": null,
  "trace_id": "b8f8fca1-4b26-4d30-a0a8-3fd7f6e6b6cf",
  "server_time": "2026-03-17T10:00:00+08:00"
}
```

### 7.1 创建专题

`POST /charging/admin/api/planning/topics`

请求：

```json
{
  "topic_name": "交能融合",
  "county_scope": "multi",
  "description": "2026 年县域交能融合规划专题"
}
```

成功响应 `data`：

```json
{
  "topic": {
    "id": 101,
    "topic_name": "交能融合",
    "county_scope": "multi",
    "status": "active"
  }
}
```

失败响应 `error`（重复）：

```json
{
  "code": "TOPIC_NAME_DUPLICATE",
  "message": "专题名称已存在"
}
```

### 7.2 创建版本

`POST /charging/admin/api/planning/versions`

请求：

```json
{
  "topic_id": 101,
  "version_name": "V1",
  "base_version_id": null
}
```

成功响应 `data`：

```json
{
  "version": {
    "id": 201,
    "topic_id": 101,
    "version_name": "V1",
    "stage": "draft"
  }
}
```

### 7.3 导入批次

`POST /charging/admin/api/geocode/batches/import`（multipart/form-data）

请求字段：

1. `file`: CSV 文件  
2. `topic_id`: 101  
3. `version_id`: 201  
4. `mapping`: `{"point_name":"name","raw_address":"address","county":"county","township":"township"}`

成功响应 `data`：

```json
{
  "batch_id": 301,
  "accepted_count": 980,
  "rejected_count": 20,
  "rejected_rows": [
    {"row": 18, "reason": "raw_address 为空"}
  ]
}
```

### 7.4 启动批量定位

`POST /charging/admin/api/geocode/batches/301/start`

请求：

```json
{
  "provider_policy": "primary_then_secondary",
  "retry_policy": {"max_retries": 3},
  "candidate_topn": 3
}
```

成功响应 `data`：

```json
{
  "job_id": "job_301_20260317_100001",
  "batch_status": "running"
}
```

### 7.5 查询批次进度

`GET /charging/admin/api/geocode/batches/301/progress`

成功响应 `data`：

```json
{
  "batch_id": 301,
  "status": "running",
  "total": 980,
  "geocoding": 120,
  "auto_pass": 620,
  "need_review": 180,
  "failed": 60,
  "published": 0,
  "progress_percent": 93.88
}
```

### 7.6 待矫正任务列表

`GET /charging/admin/api/geocode/tasks?batch_id=301&status=need_review&page=1&limit=20`

成功响应 `data`：

```json
{
  "items": [
    {
      "id": 9001,
      "point_name": "XX物流中心",
      "raw_address": "XX镇XX路",
      "confidence_score": 0.71,
      "geocode_status": "need_review"
    }
  ],
  "total": 180,
  "page": 1,
  "limit": 20
}
```

### 7.7 获取候选坐标

`GET /charging/admin/api/geocode/tasks/9001/candidates`

成功响应 `data`：

```json
{
  "candidates": [
    {"candidate_id": 1, "lon": 117.1234, "lat": 28.5678, "score": 0.82, "is_in_county_polygon": true},
    {"candidate_id": 2, "lon": 117.2234, "lat": 28.6678, "score": 0.79, "is_in_county_polygon": false}
  ]
}
```

### 7.8 采用候选坐标

`POST /charging/admin/api/geocode/tasks/9001/choose-candidate`

请求：

```json
{
  "candidate_id": 1,
  "note": "人工确认候选 1"
}
```

成功响应 `data`：

```json
{
  "task": {
    "id": 9001,
    "geocode_status": "manual_confirmed",
    "longitude": 117.1234,
    "latitude": 28.5678,
    "is_manual": true
  }
}
```

### 7.9 手工点选坐标

`POST /charging/admin/api/geocode/tasks/9001/manual-point`

请求：

```json
{
  "longitude": 117.1234,
  "latitude": 28.5678,
  "note": "地图点选修正"
}
```

失败示例（边界外）：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "OUT_OF_BOUNDARY",
    "message": "坐标不在目标县域边界内"
  }
}
```

### 7.10 失败重试

`POST /charging/admin/api/geocode/batches/301/retry-failed`

请求：

```json
{
  "max_retry": 3,
  "provider_policy": "primary_then_secondary"
}
```

成功响应 `data`：

```json
{
  "requeued_count": 42
}
```

### 7.11 发布点位

`POST /charging/admin/api/geocode/batches/301/publish`

请求：

```json
{
  "layer_type_id": 3,
  "overwrite_policy": "no_overwrite",
  "default_attributes": {
    "topic_id": 101,
    "version_id": 201,
    "plan_year": 2026
  }
}
```

成功响应 `data`：

```json
{
  "published_count": 758,
  "skipped_count": 4,
  "point_ids": [10001, 10002, 10003]
}
```

失败示例（存在未确认点）：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "UNRESOLVED_POINTS_EXIST",
    "message": "仍有 need_review/failed 点位，禁止发布"
  }
}
```

### 7.12 锁定版本

`POST /charging/admin/api/planning/versions/201/lock`

请求：

```json
{
  "lock_reason": "完成评审，进入发布冻结"
}
```

成功响应 `data`：

```json
{
  "version": {
    "id": 201,
    "stage": "locked"
  }
}
```

---

## 8. 测试与验收阈值（定版）

### 8.1 质量阈值

1. 首轮自动通过率 `>= 70%`  
2. 人工矫正后最终可发布率 `>= 95%`  
3. 边界外错误点发布拦截率 `= 100%`  

### 8.2 性能阈值

1. `1000` 条样本批次完整执行可稳定完成  
2. 进度统计与最终发布计数一致（误差 0）  
3. 同时运行 2 个批次不串数据  

### 8.3 可靠性阈值

1. 主服务不可用时自动切备服务成功率 `>= 99%`  
2. 所有人工确认动作可追溯（操作人、时间、前后状态）  

---

## 9. 对其他模型的最小输入包

将以下内容一起提供给其他模型，可直接进入实现阶段：

1. 本文档 `PLANNING_GEOCODE_MVP_DESIGN_2026-03-17.md`  
2. 现有系统路由与服务文件路径（`admin/routes.py`, `admin/services/*.py`）  
3. 测试数据包规范（12 个 CSV 包）  
4. 当前数据库表结构与命名约束  

---

## 10. 变更记录

1. v1.1（2026-03-17）补齐接口样例、硬状态规则、发布策略、主备参数、边界口径、阈值基线。  
2. v1.0（2026-03-17）初版流程与模型定义。  


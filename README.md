# 嘭咔智能电子物料仓库管理系统

PengkaMaterialWeb 是面向公司局域网的电子物料协同管理系统。员工通过浏览器访问同一套 PostgreSQL 数据；库存只能经服务端事务变更，每次成功变更都有库存流水、操作人、请求 ID 和幂等键，不依赖公网域名、CDN 或在线登录服务。

## 已实现功能

- 独立员工账号、Argon2id 密码、HttpOnly 会话、CSRF、登录失败锁定、首次登录改密、角色权限后端校验；
- 物料、分类树、库位树、供应商、项目、BOM、采购单、附件、用户和角色管理；
- 可视化库位支持标准 56 格元件盒、左右可配置混合盒，以及 20 行 × 5 列的 100 抽货架；每个格口或抽屉可直接维护物料名称、数量和备注；
- 入库、出库、报废、退料、预留、取消预留、预留转出库、盘点、库位转移、冲正；
- PostgreSQL 行级锁、事务回滚、非负库存约束和“用户 + 接口 + 幂等键”唯一约束；
- 库存流水、低库存、采购建议、仪表盘、30 天趋势、审计日志；
- CSV/XLSX/XLS 预览导入、CSV 导出、附件持久化；
- Alembic、Docker Compose、Nginx 同源入口、健康检查、每日数据库和附件备份、恢复前保护性备份；
- Vue 3 中文响应式界面、固定表头、分页、筛选、移动端适配。

## 架构与目录

```text
浏览器 -> Nginx(:80) -> Vue 静态站点
                    \-> FastAPI(/api/v1) -> PostgreSQL
                                           -> storage/attachments
定时备份容器 -> storage/backups（数据库 + 附件 + SHA-256 清单）
```

```text
backend/        FastAPI、SQLAlchemy、Alembic、脚本与 pytest
frontend/       Vue 3、TypeScript、Element Plus、ECharts、Vitest
nginx/          局域网同源反向代理
deploy/         Linux/PowerShell 备份恢复工具
storage/        附件、导入、导出和备份持久化目录
docs/           架构、数据库、API、安全、部署和验收文档
docker-compose.yml
```

详细设计见 [架构文档](docs/ARCHITECTURE.md)、[数据库文档](docs/DATABASE.md)、[API 文档](docs/API.md) 和 [安全说明](docs/SECURITY.md)。

## 环境要求

- 生产/局域网：Docker Engine 24+ 与 Docker Compose v2；建议 2 核 CPU、4 GB 内存、20 GB 可用磁盘；
- Windows：Windows 10/11、WSL 2、Docker Desktop；
- 本地源码开发：Python 3.12、Node.js 22、pnpm 11；
- 客户端：公司局域网内的现代浏览器，不安装客户端。

## 首次部署

Linux/macOS：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，至少把 `POSTGRES_PASSWORD` 和 `DATABASE_URL` 中的密码同时替换为同一个长随机密码。不要提交 `.env`。然后：

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/create_admin.py
docker compose ps
docker compose logs -f
```

后端容器启动时也会自动执行 `alembic upgrade head` 和默认角色/分类/库位初始化，因此手动迁移命令可安全重复执行。创建管理员脚本默认交互读取密码；也可临时传入 `ADMIN_USERNAME`、`ADMIN_FULL_NAME`、`ADMIN_PASSWORD`，创建后应移除敏感环境变量。

浏览器访问：`http://服务器局域网IP`，例如 `http://192.168.1.50`。默认 Web 端口为 `80`，PostgreSQL 不映射到宿主机，员工电脑无法直接连接数据库。OpenAPI 文档位于 `http://服务器IP/api/docs`。

## Windows 局域网部署

1. 在 Windows 功能中启用“适用于 Linux 的 Windows 子系统”和“虚拟机平台”，管理员 PowerShell 运行 `wsl --install`，重启；
2. 安装 Docker Desktop，设置中启用 WSL 2 引擎，并勾选“开机启动 Docker Desktop”；
3. 复制项目，执行 `Copy-Item .env.example .env`，修改密码，再执行上述 Compose 命令；
4. 运行 `ipconfig` 查找服务器的 IPv4 地址；在“高级安全 Windows Defender 防火墙”创建 TCP 入站规则，仅允许“专用网络”的端口 80；
5. 在路由器为服务器网卡 MAC 设置 DHCP 地址保留，或由管理员配置固定 IP；不要随意改公司网关/DNS；
6. 用同一 Wi-Fi/有线网的另一台电脑访问 `http://该IPv4地址`；若失败，依次检查网络配置文件是否为“专用”、防火墙、Docker Desktop、`docker compose ps` 和 `docker compose logs nginx backend`；
7. 数据库在 Docker 命名卷 `postgres_data`；附件与备份在项目的 `storage/attachments` 和 `storage/backups`。迁移服务器时必须同时迁移备份和附件。

完整步骤与固定 IP、故障排查见 [局域网部署文档](docs/LAN_DEPLOYMENT.md)。

## Linux 局域网部署

安装 Docker Engine 与 Compose 插件后复制项目，创建 `.env` 并运行首次部署命令。Ubuntu 防火墙示例：

```bash
sudo ufw allow from 192.168.0.0/16 to any port 80 proto tcp
sudo ufw enable
sudo systemctl enable --now docker
```

使用 Netplan/NetworkManager 设置固定 IP，或优先在路由器配置 DHCP 地址保留。更新版本前先备份：

```bash
./deploy/backup/backup.sh
docker compose pull
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

## 环境变量

| 变量 | 说明 | 默认/示例 |
|---|---|---|
| `POSTGRES_DB/USER/PASSWORD` | 数据库名、账号、强密码 | 必须修改密码 |
| `DATABASE_URL` | SQLAlchemy 连接串 | 与上面密码一致 |
| `WEB_PORT` | 局域网 Web 端口 | `80` |
| `COOKIE_SECURE` | HTTPS 部署时设为 true | `false` |
| `SESSION_HOURS` | 登录会话时长 | `8` |
| `MAX_UPLOAD_MB` | 单附件限制 | `20` |
| `BACKUP_SCHEDULE` | cron 表达式 | 每天 02:00 |
| `BACKUP_RETENTION_DAYS` | 自动保留天数 | `30` |

## 用户和权限

内置系统管理员、仓库管理员、硬件工程师、项目负责人和采购人员角色。管理员可创建自定义角色，也可在“用户与角色”页面修改现有角色的分组权限。前端隐藏无权限菜单以改善体验，真正的权限判断始终在 API 依赖中完成；未登录返回 401，无权限返回 403。每名员工必须使用独立账号，禁止共享账号。

删除用户采用保留历史业务关系的安全删除：账号立即失效、现有会话全部撤销、用户从列表隐藏，但库存流水、项目和审计日志仍可追溯。系统禁止删除当前登录账号，并阻止删除或权限调整导致最后一名权限管理员消失。

## CSV / Excel 导入格式

CSV 使用 UTF-8（可带 BOM），XLSX 和旧版 XLS 使用首个工作表。首行至少有 `code,name`；可选列：

```csv
code,name,mpn,package,unit,quantity,safety_stock,target_stock
MAT-R-0001,10kΩ 电阻,RC0603FR-0710KL,0603,pcs,200,100,500
```

先调用预览检查，确认后提交。新物料的 `quantity` 大于 0 时使用统一库存服务写“初始库存”流水；重复编码跳过，不覆盖现有正式数据。单批最多 5000 行。

## 备份与恢复

Compose 中 `backup` 容器默认每天 02:00 备份 PostgreSQL 和附件，生成同时间戳的 `.dump`、`.tar.gz` 与包含 SHA-256 的 JSON 清单，默认保留 30 天。手动执行：

```bash
./deploy/backup/backup.sh
./deploy/restore/restore.sh storage/backups/db_2026-07-20_020000.dump
```

PowerShell：

```powershell
.\deploy\backup\backup.ps1
.\deploy\restore\restore.ps1 storage/backups/db_2026-07-20_020000.dump
```

恢复脚本会先备份现有数据、停后端、恢复数据库和同时间戳附件、再启动后端。恢复属于破坏性操作，必须先在测试服务器演练并核对清单哈希。详细说明见 [备份恢复文档](docs/BACKUP_RESTORE.md)。

**RAID 不是备份。正式数据至少应额外保存到另一台物理设备（NAS 或另一台受控电脑），并定期做恢复演练。**

## 开发、测试与更新

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Linux: .venv/bin/pip
.venv/Scripts/python -m ruff check app scripts tests
.venv/Scripts/python -m pytest

cd ../frontend
pnpm install --frozen-lockfile
pnpm run lint
pnpm test
pnpm run build
```

PostgreSQL 并发测试需要独立测试库：设置 `TEST_POSTGRES_URL` 后运行 `pytest tests/concurrency`。禁止指向生产库。更新前执行备份，更新代码后重新构建并迁移，最后检查健康状态和关键业务。

## 常见问题与安全注意

- 页面打不开：检查客户端能否 ping 服务器、端口 80 防火墙、`docker compose ps`、Nginx 日志；
- API 502：检查 `backend` 与 `db` 健康状态、`.env` 两处数据库密码是否一致；
- 登录 403/CSRF：清理该站点 Cookie 后重新登录，确保前后端经同一地址访问；
- 数据库空间不足：清理旧备份前先复制到另一物理设备，检查附件大文件；
- 不要把 5432 映射到员工网段，不要提交 `.env`，不要通过物料编辑接口修库存；
- HTTPS 部署时设 `COOKIE_SECURE=true`，由内部 CA 或受控反向代理终止 TLS；
- 定期停用离职账号、审阅管理员和仓库角色、查看登录失败及审计日志。

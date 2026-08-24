# 局域网部署手册

Windows：安装 Docker Desktop 和 WSL 2，启用虚拟化；复制 `.env.example`，同时修改数据库密码和连接串；构建启动、迁移、交互创建管理员；用 `ipconfig` 获取 IPv4；只在 Windows 防火墙“专用”配置文件允许 TCP 80；设置 DHCP 地址保留；从另一台员工电脑测试；启用 Docker Desktop 开机启动；数据位置分别为 Docker 卷、`storage/attachments`、`storage/backups`。

Linux：从 Docker 官方仓库安装 Engine 与 Compose 插件；将项目放在受限服务账号目录；创建 `.env`（建议权限 600）；运行 Compose；用 ufw/firewalld 只允许公司网段访问 Web；用路由器保留地址或 Netplan 配固定 IP；`systemctl enable docker`。更新前备份，更新后迁移、检查 `docker compose ps`、健康接口、登录和一次测试库存操作。

内部名称 `material.local` 可由公司 DNS 指向固定 IP；不要依赖公网 DNS。故障顺序：供电/磁盘 → Docker 服务 → 容器状态 → db/backend/nginx 日志 → 防火墙/VLAN → 浏览器 Cookie。若数据库认证失败，核对 `.env` 和已存在数据库卷的原始密码；修改 `.env` 不会自动修改旧数据库用户密码。

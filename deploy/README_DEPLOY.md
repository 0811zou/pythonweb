我已将部署脚本和生产 docker-compose、Nginx 模板和 .env.example 推送到 feat/agro-mvp 分支。

下一步你需要在 VM 上执行（示例）：
1. 登录 VM，确保已安装 Docker & docker-compose 插件（如果未安装，我在 README 中已有安装步骤）。
2. 将仓库克隆到 /opt/pythonweb（或你喜欢的目录），并切换到 feat/agro-mvp 分支：
   git clone https://github.com/0811zou/pythonweb.git /opt/pythonweb
   cd /opt/pythonweb
   git checkout feat/agro-mvp
3. 复制 .env.example 为 .env.production 并编辑：
   cp .env.example .env.production
   # 编辑 SECRET_KEY, POSTGRES_PASSWORD, ALLOWED_HOSTS 等
4. 编辑 deploy/nginx/conf.d/web.conf，将 REPLACE_WITH_YOUR_DOMAIN 替换为你的域名
5. 运行自动部署脚本（需有 sudo 权限）：
   sudo bash deploy/deploy.sh

我无法直接登录或在你的 VM 上执行命令，但如果你在执行过程中粘贴错误或日志，我会在这里实时协助你排错。

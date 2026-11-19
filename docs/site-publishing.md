# 网页维护与发布

线上入口：https://bubblevv.github.io/ai-api-gongyi-nav/

GitHub Pages 从 `main` 分支根目录发布，服务的是已生成的静态文件，无需数据库或常驻后端。

## 日常新增

把站名和带邀请参数的推广链接发给助手即可，标签和备注可选。使用仓库内 `publish-ai-site` 技能进行预检、去重、生成、测试、提交和推送。

```text
站点：示例 API
链接：https://api.example.com/register?aff=example
标签：公益;签到;GPT
备注：站方文案中的额度或使用说明
```

数据源是 `ai-api-sites-table.xlsx`。页面、README、Markdown、CSV、JSON 和分享封面都由生成器更新。新增时自动记录添加日期；日期越新排得越靠前，同一天按序号倒序。没有添加日期的历史记录放在最后并保留原序号顺序，不根据备注猜测日期。

## 网页样式调整

- 修改 `tools/site_template.html` 调整布局、颜色和筛选交互。
- 修改 `tools/generate_site.py` 调整排序、输出字段、页面摘要和结构化数据。
- 重新生成：`python tools/generate_site.py`。
- 检查：`python -m unittest discover -s tests` 和 `git diff --check`。
- 在浏览器检查桌面、手机、搜索、标签筛选、空结果和禁用 JavaScript 时的目录。
- 只暂存本次明确修改的文件，保留工作区其他未提交文件。

## 发布与验证

向 `main` 提交并推送生成结果后，GitHub Pages 自动发布。通过 `gh api repos/bubblevv/ai-api-gongyi-nav/pages/builds/latest` 查看最新构建，并请求线上首页确认最新条目和页面内容。

搜索引擎可直接读取完整 HTML、站点名称、备注和推广链接。首页包含 canonical、分享元信息和 JSON-LD，仓库根目录包含 `sitemap.xml`。

项目路径下的 `robots.txt` 不是 GitHub 用户根域的机器人规则文件；不把它当作已成功提交站点地图的证明。若要主动提交站点地图，可由拥有相应账户权限的人在搜索引擎站长平台验证网站后提交：

```text
https://bubblevv.github.io/ai-api-gongyi-nav/sitemap.xml
```

网页可抓取不等于已被搜索引擎收录，不能保证收录时间或搜索排名。

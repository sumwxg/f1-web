# APEX F1 Live

公开 F1 数据网站。页面不含手工赛果或模拟新闻。

## 数据来源

- 赛历、正式赛果、车手积分、车队积分：Jolpica（Ergast-compatible public API）
- 赛事新闻：Google News RSS

每个接口在 Vercel 服务端缓存，避免浏览器跨域问题。若任一来源不可用，页面显示数据源错误，不会以示例数据替代。

## 部署

导入该 GitHub 仓库至 Vercel，框架预设选择 `Other`，不需要构建命令或环境变量。部署后，打开 Vercel 提供的公开 URL 即可。

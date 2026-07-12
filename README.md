# APEX F1 Live

公开 F1 数据网站。页面不含手工赛果或模拟新闻。

## 数据来源

- 赛历、正式赛果、车手积分、车队积分：Jolpica（Ergast-compatible public API）
- 赛事新闻：Google News RSS

每个接口在 Vercel 服务端缓存，避免浏览器跨域问题。若任一来源不可用，页面显示数据源错误，不会以示例数据替代。

## 部署

导入该 GitHub 仓库至 Vercel，框架预设选择 `Other`，不需要构建命令或环境变量。部署后，打开 Vercel 提供的公开 URL 即可。

## 安装为桌面端 / 手机端软件

部署网站采用 PWA 标准。

- Windows / macOS：使用 Chrome 或 Edge 打开网站，点击地址栏右侧的“安装”图标，或页面右上方“安装应用”。
- Android：在 Chrome 菜单中选择“安装应用”或“添加到主屏幕”。
- iPhone / iPad：在 Safari 点“分享”，选择“添加到主屏幕”。

安装后将以独立窗口运行，并缓存应用外壳；赛果与新闻仍需网络连接以保持真实数据。

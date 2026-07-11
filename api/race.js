const plain = value => (value || '').replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
const tag = (xml, name) => plain((xml.match(new RegExp(`<${name}[^>]*>([\\s\\S]*?)</${name}>`)) || [])[1] || '');
const articlesFromRss = xml => [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].slice(0, 8).map(match => {
  const item = match[1];
  return { title: tag(item, 'title'), url: tag(item, 'link'), published: tag(item, 'pubDate'), source: tag(item, 'source') || 'Google News' };
}).filter(article => article.title && article.url);

export default async function handler(request, response) {
  const year = /^20\d{2}$/.test(request.query.year || '') ? request.query.year : '2026';
  const round = String(request.query.round || '');
  if (!/^\d{1,2}$/.test(round)) return response.status(400).json({ error: '无效的比赛编号。' });
  response.setHeader('Cache-Control', 's-maxage=900, stale-while-revalidate=3600');
  try {
    const raceResponse = await fetch(`https://api.jolpi.ca/ergast/f1/${year}/${round}/results.json?limit=100`, { headers: { 'User-Agent': 'APEX-F1-Live/1.0' } });
    if (!raceResponse.ok) throw new Error(`赛果源返回 ${raceResponse.status}`);
    const raw = await raceResponse.json();
    const race = raw.MRData?.RaceTable?.Races?.[0] || null;
    const query = encodeURIComponent(`${year} ${race?.raceName || 'Formula 1'} Formula 1`);
    let articles = [];
    try {
      const newsResponse = await fetch(`https://news.google.com/rss/search?q=${query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans`, { headers: { 'User-Agent': 'Mozilla/5.0 APEX-F1-Live/1.0' } });
      if (newsResponse.ok) articles = articlesFromRss(await newsResponse.text());
    } catch { /* Race results remain available if news is temporarily unavailable. */ }
    response.status(200).json({ year, source: 'Jolpica + Google News RSS', updatedAt: new Date().toISOString(), race, articles });
  } catch (error) {
    response.status(502).json({ error: '无法加载该场比赛的真实数据。', detail: error.message });
  }
}

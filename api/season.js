const isYear = value => /^20\d{2}$/.test(value || '') ? value : '2026';
const fetchJson = async url => {
  const response = await fetch(url, { headers: { 'User-Agent': 'APEX-F1-Live/1.0' } });
  if (!response.ok) throw new Error(`数据源返回 ${response.status}`);
  return response.json();
};

export default async function handler(request, response) {
  const year = isYear(request.query.year);
  const base = `https://api.jolpi.ca/ergast/f1/${year}`;
  response.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=900');
  try {
    const [calendar, results, drivers, constructors] = await Promise.all([
      fetchJson(`${base}.json?limit=100`),
      fetchJson(`${base}/results.json?limit=1000`),
      fetchJson(`${base}/driverstandings.json?limit=100`),
      fetchJson(`${base}/constructorstandings.json?limit=100`),
    ]);
    response.status(200).json({
      year,
      updatedAt: new Date().toISOString(),
      source: 'Jolpica (Ergast-compatible public API)',
      calendar: calendar.MRData?.RaceTable?.Races || [],
      results: results.MRData?.RaceTable?.Races || [],
      driverStandings: drivers.MRData?.StandingsTable?.StandingsLists?.[0]?.DriverStandings || [],
      constructorStandings: constructors.MRData?.StandingsTable?.StandingsLists?.[0]?.ConstructorStandings || [],
    });
  } catch (error) {
    response.status(502).json({ error: '无法从公开 F1 数据源同步，请稍后重试。', detail: error.message });
  }
}

import React, { useState } from 'react';

function App() {
  const [eventUrl, setEventUrl] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [autoResult, setAutoResult] = useState(null);

  const searchEvent = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch('http://127.0.0.1:5000/search_event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-TOKEN': 'my_secret_token'
        },
        body: JSON.stringify({ keyword: eventUrl }) // 這裡暫時用 eventUrl 當作搜尋關鍵字
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError('API 請求失敗，請確認後端已啟動');
    } finally {
      setLoading(false);
    }
  };

  const autoTicket = async () => {
    setLoading(true);
    setError(null);
    setAutoResult(null);
    try {
      const res = await fetch('http://127.0.0.1:5000/auto_ticket', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-TOKEN': 'my_secret_token'
        },
        body: JSON.stringify({
          url: eventUrl,
          area_keywords: ["A區"], // 可改成你要的區域
          price_keywords: ["5400"], // 可改成你要的價格
          ticket_count: 1 // 可改成你要的張數
        })
      });
      const data = await res.json();
      setAutoResult(data);
    } catch (err) {
      setError('API 請求失敗，請確認後端已啟動');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24, maxWidth: 480, margin: '0 auto', fontFamily: 'sans-serif' }}>
      <h2>tixCraft 自動搶票前端 (React)</h2>
      <div style={{ marginBottom: 16 }}>
        <input
          value={eventUrl}
          onChange={e => setEventUrl(e.target.value)}
          placeholder="輸入藝人活動頁面網址 (如 https://tixcraft.com/activity/detail/xxx)"
          style={{ padding: 8, width: '70%', marginRight: 8 }}
        />
        <button onClick={searchEvent} disabled={loading || !eventUrl} style={{ padding: 8 }}>
          {loading ? '搜尋中...' : '搜尋活動'}
        </button>
      </div>
      {error && <div style={{ color: 'red', marginBottom: 8 }}>{error}</div>}
      {result && (
        <div style={{ background: '#f6f6f6', padding: 12, borderRadius: 4, marginBottom: 16 }}>
          <strong>API 回傳：</strong>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
      <hr style={{ margin: '24px 0' }} />
      <div style={{ marginBottom: 16 }}>
        <input
          value={eventUrl}
          onChange={e => setEventUrl(e.target.value)}
          placeholder="輸入藝人活動頁面網址 (如 https://tixcraft.com/activity/detail/xxx)"
          style={{ padding: 8, width: '70%', marginRight: 8 }}
        />
        <button onClick={autoTicket} disabled={loading || !eventUrl} style={{ padding: 8, background: '#4caf50', color: 'white' }}>
          {loading ? '執行中...' : '一鍵自動搶票'}
        </button>
      </div>
      {autoResult && (
        <div style={{ background: '#e8f5e9', padding: 12, borderRadius: 4 }}>
          <strong>自動搶票結果：</strong>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{JSON.stringify(autoResult, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;

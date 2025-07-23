import React, { useState } from 'react';
import { AppBar, Toolbar, Typography, Container, Card, CardContent, TextField, Button, CircularProgress, Box, CssBaseline, ThemeProvider, createTheme, Paper } from '@mui/material';
import KpopIcon from '@mui/icons-material/MusicNote';
import TicketIcon from '@mui/icons-material/ConfirmationNumber';
import FavoriteIcon from '@mui/icons-material/Favorite';

const theme = createTheme({
  palette: {
    primary: {
      main: '#d500f9',
    },
    secondary: {
      main: '#ff4081',
    },
    background: {
      default: '#f3e5f5',
    },
  },
  typography: {
    fontFamily: '"Segoe UI", "Noto Sans TC", "Arial", sans-serif',
    h2: {
      fontWeight: 700,
      letterSpacing: 2,
    },
  },
});

function App() {
  const [input, setInput] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [autoResult, setAutoResult] = useState(null);

  const isUrl = (str) => /^https?:\/\//.test(str);

  // 搜尋活動（用 input 當 keyword）
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
        body: JSON.stringify({ keyword: input })
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError('API 請求失敗，請確認後端已啟動');
    } finally {
      setLoading(false);
    }
  };

  // 自動搶票（用 input 當 url）
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
          url: input,
          area_keywords: ["A區"],
          price_keywords: ["5400"],
          ticket_count: 1
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

  // 智能搜尋：若為網址則自動搶票，否則搜尋活動
  const handleSearch = () => {
    if (isUrl(input)) {
      autoTicket();
    } else {
      searchEvent();
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static" color="primary" elevation={2}>
        <Toolbar>
          <KpopIcon sx={{ mr: 2, fontSize: 32 }} />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700, letterSpacing: 2 }}>
            KPOP搶票神器
          </Typography>
          <FavoriteIcon sx={{ color: '#ff4081', fontSize: 28, mr: 1 }} />
          <TicketIcon sx={{ color: '#fff176', fontSize: 28 }} />
        </Toolbar>
      </AppBar>
      <Container maxWidth="sm" sx={{ mt: 5, mb: 5 }}>
        <Card sx={{ borderRadius: 4, boxShadow: 6, mb: 3 }}>
          <CardContent>
            <Typography variant="h4" align="center" gutterBottom sx={{ fontWeight: 700, color: 'primary.main' }}>
              KPOP 🎤 自動搶票平台
            </Typography>
            <Typography align="center" sx={{ mb: 2, color: 'secondary.main' }}>
              為粉絲而生，搶票不再手忙腳亂！💜
            </Typography>
            {/* 單一輸入框區塊 */}
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TextField
                label="藝人名稱或活動網址"
                variant="outlined"
                fullWidth
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="如 鄭準元 或 https://tixcraft.com/activity/detail/xxx"
                sx={{ mr: 2, background: '#fff', borderRadius: 2 }}
                InputProps={{ startAdornment: <KpopIcon sx={{ color: 'primary.main', mr: 1 }} /> }}
              />
              <Button
                onClick={handleSearch}
                disabled={loading || !input}
                variant="contained"
                color="secondary"
                size="large"
                sx={{ minWidth: 120, fontWeight: 700, borderRadius: 2 }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : '搜尋活動'}
              </Button>
            </Box>
            {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}
            {(result || autoResult) && (
              <Paper sx={{ background: '#f6f6f6', p: 2, borderRadius: 2, mb: 2 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>API 回傳：</Typography>
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0 }}>{JSON.stringify(result || autoResult, null, 2)}</pre>
              </Paper>
            )}
            {/* 自動搶票按鈕區塊 */}
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
              <Button
                onClick={autoTicket}
                disabled={loading || !input}
                variant="contained"
                color="primary"
                size="large"
                sx={{ minWidth: 120, fontWeight: 700, borderRadius: 2 }}
                startIcon={<TicketIcon />}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : '一鍵自動搶票'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Container>
      <Box component="footer" sx={{ py: 3, textAlign: 'center', background: 'linear-gradient(90deg, #d500f9 60%, #ff4081 100%)', color: '#fff' }}>
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          KPOP搶票神器 | Powered by Python & React | For All KPOP Fans 💜
        </Typography>
      </Box>
    </ThemeProvider>
  );
}

export default App;

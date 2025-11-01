# ElektrAize Frontend

Modern giriş arayüzü (lacivert ve gri tonlarında), filtreleme ve gece modu ile.

## Geliştirme

```bash
cd frontend
npm install
npm run dev
```

Varsayılan olarak `http://localhost:5173` adresinde çalışır. `--host` ile yerel ağda yayınlayabilirsiniz.

## Özellikler
- Modern arayüz, lacivert/gri tema
- Filtreleme: Arama kutusuyla kartları filtreleyin
- Gece modu: Üst barda buton ile aç/kapa, localStorage ile hatırlanır

## Teknolojiler
- React + TypeScript + Vite
- Tailwind CSS (dark mode: `class`)

## Stil ve Tema
- Ana lacivert tonları: `navy-900`, `navy-800`, `navy-700`
- Gri tonları: `gray-900` → `gray-100`

## Üretim (Build)

```bash
npm run build
npm run preview
```

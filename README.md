# RECOVERY YOUTUBE

Обход блокировки YouTube через VLESS-подписку (split-tunnel: через VPN идут только сайты YouTube, остальной интернет не затрагивается).

Unblock YouTube via VLESS subscription (split-tunnel: only YouTube traffic goes through VPN, the rest of the Internet is unaffected).

## Быстрый старт (Windows)

1. Скачайте `RECOVERY_YOUTUBE.exe` из [Releases](https://github.com/innokentyRECOVERY/RECOVERY-YOUTUBE/releases).
2. Запустите его и нажмите «ЗАПУСТИТЬ ОБХОД».
3. При первом запуске автоматически скачается `xray-core` (нужен доступ к GitHub).
4. Откройте YouTube — он будет работать.

## Что делает программа

- Подключается к серверу Англия из VLESS-подписки.
- Split-tunnel: только домены YouTube (`youtube.com`, `googlevideo.com`, `ytimg.com`, `youtu.be` и др.) идут через VPN, весь остальной трафик — напрямую.
- Показывает реальную скорость трафика (⬆ отдаёт / ⬇ получает).
- Лимит сессии 2 часа с автоотключением, повторный запуск — вручную.
- Поддержка смены кода подписки без перезапуска.

## Как это работает

- GUI на `tkinter` (Python).
- Ядро — [Xray-core](https://github.com/XTLS/Xray-core), скачивается автоматически.
- Системный прокси WinINET ставится на `127.0.0.1:10809`, только для процессов, использующих системный прокси.

## Сборка из исходников

```
pip install pyinstaller
pyinstaller --onefile --windowed --name RECOVERY_YOUTUBE RECOVERYYOUTUBE.py
```

## Важно

- Подписка нуждается в действующем коде (вводится в поле «Новый код подписки»).
- При закрытии программы системный прокси снимается автоматически.
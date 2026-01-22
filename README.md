# Game Rock-Paper-Scissors (Nhóm 16)

Dự án này là một triển khai trò chơi "Kéo - Búa - Bao" (Rock-Paper-Scissors) hỗ trợ giao diện client và server để chơi nhiều người hoặc chơi với máy.

**Mục tiêu**
- Cung cấp server đơn giản để kết nối nhiều client (máy tính/GUI) và quản lý vòng chơi.
- Cung cấp client GUI để người dùng tương tác và gửi lựa chọn (kéo/búa/bao).

**Cấu trúc dự án**
- `server.py` — entrypoint server ở repo gốc (cũng có folder `server/` với mã chi tiết).
- `client_gui.py` — client GUI mẫu ở repo gốc.
- `client/` — mã client (gồm `gui.py`, `main.py`, `network.py`, `constants.py`).
- `server/` — mã server (gồm `main.py`, `server_logic.py`, `game_logic.py`, `constants.py`).

**Yêu cầu (Prerequisites)**
- Python 3.8+
- Các thư viện Python trong `requirements.txt` (nếu có). Nếu chưa có file, cài từng package theo lỗi khi chạy.

**Chạy nhanh (Local)**
1. Tạo và kích hoạt virtualenv (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Cài dependencies (nếu có `requirements.txt`):

```powershell
pip install -r requirements.txt
```

3. Chạy server (từ thư mục gốc):

```powershell
python server.py
```

4. Chạy client GUI (mở thêm terminal):

```powershell
python client_gui.py
```

Hoặc chạy các entrypoint riêng trong `client/` và `server/` nếu bạn muốn debug chi tiết.

**Kiến nghị phát triển**
- Tách rõ API mạng (HTTP / WebSocket / TCP) trong `server/` để dễ thay đổi khi triển khai cloud.
- Thêm file `requirements.txt` hoặc `pyproject.toml` để quản lý dependency.
- Tạo script khởi động trong `scripts/` hoặc task cho VSCode để đơn giản hoá việc chạy dev.

**Triển khai và hướng đi với Cloudflare**

Dưới đây là một số hướng đi và bước gợi ý để triển khai dự án lên môi trường sử dụng Cloudflare. Chọn chiến lược phù hợp với kiểu kết nối mà server của bạn dùng (HTTP/WebSocket vs raw TCP/UDP).

- **Tùy chọn 1 — Cloudflare Tunnel (được khuyên dùng cho dev và dịch vụ không-public):**
  - Mô tả: Dùng `cloudflared` (Cloudflare Tunnel) để mở một tunnel an toàn từ máy chủ cục bộ tới miền do Cloudflare quản lý. Hỗ trợ HTTP/HTTPS và WebSocket rất tốt.
  - Khi dùng tunnel, bạn không cần mở port trực tiếp trên firewall; tunnel kết nối ra Cloudflare và map một hostname (ví dụ `rps.example.com`) tới dịch vụ cục bộ.
  - Các bước cơ bản:
    1. Tạo tài khoản Cloudflare và thêm domain (hoặc dùng domain thử nghiệm).
    2. Cài `cloudflared` trên máy chủ (Windows: dùng chocolatey `choco install cloudflared` hoặc tải binary từ Cloudflare).
    3. Đăng nhập: `cloudflared tunnel login` và chọn domain.
    4. Tạo tunnel: `cloudflared tunnel create my-rps-tunnel`.
    5. Tạo file cấu hình `config.yml` (ví dụ):

```yaml
tunnel: <TUNNEL-UUID>
credentials-file: C:\path\to\.cloudflared\<TUNNEL-UUID>.json
ingress:
  - hostname: rps.example.com
    service: http://localhost:5000
  - service: http_status:404
```

    6. Chạy tunnel: `cloudflared tunnel run my-rps-tunnel` hoặc cấu hình chạy như service.
    7. Thiết lập bản ghi DNS `CNAME` hoặc `A` trong Cloudflare nếu cần (Cloudflare có hướng dẫn tự động khi tạo tunnel).

  - Lưu ý: Nếu server dùng WebSocket qua HTTP(S), Cloudflare và Tunnel hỗ trợ chuyển tiếp WebSocket. Nếu server dùng raw TCP/UDP, cần kiểm tra các tính năng bổ sung (Cloudflare Spectrum hoặc Tunnel TCP - có giới hạn theo gói).

- **Tùy chọn 2 — Triển khai ứng dụng HTTP/WebSocket lên Cloudflare Workers + KV / Durable Objects (advanced):**
  - Mô tả: Nếu bạn có thể chuyển server thành một service HTTP hoặc websocket-like, Cloudflare Workers (kết hợp Durable Objects) có thể dùng để quản lý trạng thái nhỏ hoặc vòng chơi realtime.
  - Ưu điểm: Rất scale, low-latency, không cần quản trị server.
  - Nhược điểm: Cần re-architect (Workers dùng JavaScript/TypeScript và có giới hạn runtime).

- **Tùy chọn 3 — Cloudflare Pages (static) + API backend qua Tunnel/Worker:**
  - Dùng khi client là web tĩnh (HTML/JS). Pages host client, backend vẫn chạy trên server hoặc Cloudflare Worker.

- **Bảo mật & quản lý:**
  - Dùng Cloudflare Access để bảo vệ endpoint admin hoặc server management.
  - Kích hoạt TLS (Full/Full (strict)) cho domain trong Cloudflare.
  - Thiết lập rate-limiting và WAF (Cloudflare Firewall rules) để chống abuse.

- **DNS & routing:**
  - Sử dụng Cloudflare DNS cho tên miền; bật proxy (mây màu cam) khi muốn Cloudflare bảo hộ HTTP/WebSocket.
  - Nếu cần raw TCP/UDP, cân nhắc Cloudflare Spectrum (enterprise) hoặc dùng Tunnel TCP với giới hạn.

**Mẹo triển khai nhanh (ví dụ cụ thể)**
1. Đăng ký Cloudflare, thêm domain, đổi nameserver tại registrar.
2. Cài `cloudflared` trên máy chủ/VM có địa chỉ IP tĩnh.
3. `cloudflared tunnel login` → `cloudflared tunnel create rps-tunnel` → tạo `config.yml` → `cloudflared tunnel run rps-tunnel`.
4. Trỏ `rps.example.com` trong dashboard Cloudflare tới tunnel (Cloudflare sẽ hướng dẫn chi tiết).

**Next steps gợi ý**
- Tạo `requirements.txt` (nếu dùng Python) và đảm bảo server chạy qua HTTP/WebSocket.
- Quyết định cách kết nối: HTTP/WebSocket (dễ dùng Cloudflare) hay raw sockets (cần thêm bước với Spectrum/Tunnel).
- Mình có thể giúp: tạo `config.yml` mẫu cho `cloudflared`, hoặc viết hướng dẫn chi tiết theo cách server hiện tại kết nối (ví dụ: WebSocket endpoint vs raw TCP).

---

Liên hệ
- Tác giả: Nhóm 16

Nếu bạn muốn, mình sẽ mở rộng phần Cloudflare với các lệnh chính xác cho Windows và mẫu `service` để chạy `cloudflared` tự động.

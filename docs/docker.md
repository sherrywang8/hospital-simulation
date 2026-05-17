# Docker 啟動教學

這份文件說明如何用 Docker 在本機啟動這個專案，並整理成兩種常用模式：

- 正式模擬模式：前端會先 build，再由 Nginx 提供靜態頁面，適合驗證接近正式環境的行為。
- 開發模式：前端使用 Vite dev server，支援熱更新，適合修改前端時使用。

## 專案會啟動哪些服務

### `backend`

- 技術：FastAPI + 模擬服務
- 容器內埠號：`8000`
- 健康檢查：`/api/v1/health`
- 主要 API 根路徑：`/api/v1`

### `frontend`

- 正式模擬模式：React build 完後由 Nginx 提供
- 開發模式：Vite dev server
- 主機預設埠號：`3000`

### 產出檔案

- 模擬輸出會寫到主機端的 `data/runtime/artifacts/`
- 這個資料夾會透過 volume 掛載到 backend 容器中的 `/app/runtime/artifacts`

## 前置需求

1. 安裝 Docker Desktop。
2. 確認 Docker Desktop 已啟動。
3. 在專案根目錄執行指令，也就是目前這個資料夾：

```powershell
cd C:\hospital-simulation
```

4. 如果你想改埠號或 artifact 路徑，可以先建立 `.env`：

```powershell
Copy-Item .env.example .env
```

如果你沒有建立 `.env`，Docker Compose 也會使用預設值正常啟動。

## 預設埠號與環境變數

`.env.example` 目前的預設值如下：

```env
BACKEND_PORT=8000
FRONTEND_PORT=3000
ARTIFACTS_HOST_PATH=./data/runtime/artifacts
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

常用變數說明：

- `BACKEND_PORT`：後端 API 對外埠號
- `FRONTEND_PORT`：前端頁面對外埠號
- `ARTIFACTS_HOST_PATH`：模擬結果輸出到主機的資料夾
- `CORS_ORIGINS`：允許瀏覽器存取 backend 的來源

## 啟動前先檢查 Docker

建議先確認 Docker 與 Compose 都可用：

```powershell
docker version
docker compose version
```

如果這兩個指令能正常回應，就可以開始啟動專案。

## 方法一：正式模擬模式

這個模式會：

- 建立 `backend` image
- 建立 `frontend` image
- 啟動 backend 容器
- 等 backend 健康檢查通過後，再啟動 frontend
- 由 Nginx 將 `/api/` 代理到 backend 容器

### 啟動指令

```powershell
docker compose up --build
```

如果你想讓容器在背景執行，可以使用：

```powershell
docker compose up --build -d
```

### 成功啟動後的網址

- 前端首頁：`http://localhost:3000`
- 後端健康檢查：`http://localhost:8000/api/v1/health`
- 後端情境清單：`http://localhost:8000/api/v1/scenarios`

### 這個模式的 API 連線方式

正式模擬模式下，前端不是直接打 `localhost:8000`，而是由 Nginx 把：

- `http://localhost:3000/api/...`

代理到 backend 容器，所以你只要打開前端首頁即可正常使用。

## 方法二：開發模式

這個模式適合前端開發，因為：

- 前端改檔後會自動熱更新
- `/api` 會由 Vite proxy 轉送到 backend 容器

### 啟動指令

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

如果你要背景執行：

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

### 成功啟動後的網址

- 前端開發站：`http://localhost:3000`
- 後端 API：`http://localhost:8000/api/v1`

### 這個模式的 API 連線方式

開發模式下，前端是 Vite dev server，`/api` 會被 proxy 到：

- `http://backend:8000`

所以瀏覽器端仍然只需要打 `http://localhost:3000`。

## Windows 建議用法

這個 repo 已經提供了 PowerShell 腳本，特別適合在 Windows 上避免某些 BuildKit 或路徑相關問題。

### 正式模擬模式

```powershell
powershell -ExecutionPolicy Bypass -File .\docker\up.ps1
```

這個腳本會做四件事：

1. 關閉 `DOCKER_BUILDKIT`
2. 手動 build `ed-simulation-backend`
3. 手動 build `ed-simulation-frontend`
4. 用 `docker compose up -d --no-build` 啟動容器

### 開發模式

```powershell
powershell -ExecutionPolicy Bypass -File .\docker\up-dev.ps1
```

這個腳本會做四件事：

1. 關閉 `DOCKER_BUILDKIT`
2. build `ed-simulation-backend`
3. build `ed-simulation-frontend-dev`
4. 用 dev compose 組合啟動容器

### 停止容器

```powershell
powershell -ExecutionPolicy Bypass -File .\docker\down.ps1
```

## 啟動後如何驗證

### 檢查容器狀態

```powershell
docker compose ps
```

如果是開發模式，建議用：

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

### 檢查 backend 健康狀態

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
```

預期會回傳：

```json
{"status":"ok"}
```

### 檢查 scenario API

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/scenarios
```

### 送出一次模擬測試

```powershell
$body = @{
  scheduling_strategy = "SBP"
  num_doctors = 5
  num_doctors_night = 3
  num_nurses = 3
  num_ct = 1
  num_xray = 1
  num_lab = 1
  num_ultrasound = 1
  simulation_time = 180
  exam_probability = 0.6
  arrival_rate_multiplier = 1.0
  random_seed = 7
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/simulations `
  -ContentType "application/json" `
  -Body $body
```

如果成功，模擬結果也會被寫到：

```text
data/runtime/artifacts/
```

## 常用管理指令

### 查看 log

前景模式本來就會直接看到 log；如果你是背景啟動，可以用：

```powershell
docker compose logs -f
```

開發模式：

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
```

### 重新 build 並重啟

正式模擬模式：

```powershell
docker compose up --build -d
```

開發模式：

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

### 只停止但保留資料

```powershell
docker compose down
```

### 停止並移除 dev mode 額外 volume

開發模式會建立 `frontend_node_modules` volume；如果你想一起清掉：

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

## 常見問題排查

### 1. `docker` 指令找不到

請先確認：

- Docker Desktop 已安裝
- Docker Desktop 已啟動完成
- 重新開一個 PowerShell 視窗後再試一次

### 2. `localhost:3000` 或 `localhost:8000` 被占用

請修改 `.env`：

```env
BACKEND_PORT=18000
FRONTEND_PORT=13000
```

之後重新啟動：

```powershell
docker compose up --build -d
```

### 3. Windows 在非 ASCII 路徑下 build 失敗

如果你的專案路徑包含中文或特殊字元，Docker Desktop / BuildKit 有時會出現共享金鑰或 build 相關錯誤。這時優先改用 repo 內建腳本：

```powershell
powershell -ExecutionPolicy Bypass -File .\docker\up.ps1
```

或：

```powershell
powershell -ExecutionPolicy Bypass -File .\docker\up-dev.ps1
```

### 4. 前端頁面打得開，但 API 呼叫失敗

請依序檢查：

1. `docker compose ps` 看 `backend` 是否為 healthy
2. `Invoke-RestMethod http://localhost:8000/api/v1/health` 是否回傳 `status: ok`
3. `.env` 裡的 `BACKEND_PORT` 與 `FRONTEND_PORT` 是否改過但沒有同步重啟

### 5. 找不到 artifact 檔案

artifact 只有在你真的送出模擬請求後才會出現。先呼叫一次 `/api/v1/simulations`，再到：

```text
data/runtime/artifacts/
```

查看結果。

## 最短啟動流程

如果你只想快速跑起來，直接照下面做：

```powershell
cd C:\hospital-simulation
powershell -ExecutionPolicy Bypass -File .\docker\up.ps1
```

然後打開：

```text
http://localhost:3000
```

## 補充說明

- 正式模擬模式比較接近部署環境
- 開發模式比較適合改前端
- backend 容器健康檢查通過後，frontend 才會啟動
- 模擬結果會落在主機端的 `data/runtime/artifacts/`

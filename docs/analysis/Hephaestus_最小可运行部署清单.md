# Hephaestus 鏈€灏忓彲杩愯閮ㄧ讲娓呭崟

## 1. 鐩爣

杩欎唤娓呭崟鐨勭洰鏍囦笉鏄€滅敓浜ч儴缃测€濓紝鑰屾槸锛?

- 鍦ㄦ湰鏈烘妸 Part 1 椤圭洰璺戣捣鏉?
- 鎵撻€氬墠绔€佸悗绔€佹暟鎹簱銆丷edis 鐨勬渶灏忛摼璺?
- 楠岃瘉娉ㄥ唽銆佺櫥褰曘€佽繘鍏ラ〉闈€佸彂璧?Agent 浠诲姟杩欐潯涓昏矾寰?

褰撳墠寤鸿浠ヨВ鍘嬪悗鐨勬簮鐮佷负鍩哄噯锛?

- 鍚庣鐩綍锛歚K:\2025鍏ㄥ勾鐝璤澶фā鍨婣gent(4)\瀹炴垬椤圭洰鍥涳細鈥淢anus鈥濋€氱敤鏅鸿兘浣撻」鐩紑鍙戝疄鎴橈紙瀹岀粨锛塡_extracted\part1\backend`
- 鍓嶇鐩綍锛歚part 1` 鍘嬬缉鍖呭唴鐨?`frontend`

---

## 2. 鏈€灏忚繍琛屾墍闇€缁勪欢

浠庤浠躲€佽剼鏈拰婧愮爜鐪嬶紝鏈€灏忚繍琛屼緷璧栧涓嬶細

1. `Node.js`
2. `Python 3.11`
3. `PostgreSQL`
4. `Redis`
5. 妯″瀷 API Key

涓ユ牸鏉ヨ锛屾矙绠辨湇鍔″湪寰堝楂樼骇鑳藉姏閲屼細鐢ㄥ埌锛屼絾濡傛灉鐩爣鍙槸鍏堣窇璧锋渶灏忛摼璺紝鍙互鍏堟妸瀹冭涓虹浜岄樁娈甸厤缃」銆?

---

## 3. 鎺ㄨ崘鐨勬渶灏忚繍琛岄『搴?

鎺ㄨ崘椤哄簭濡備笅锛?

1. 鍏堝惎鍔?PostgreSQL
2. 鍐嶅惎鍔?Redis
3. 閰嶇疆鍚庣 `.env`
4. 鍒濆鍖栨暟鎹簱琛?
5. 鍚姩鍚庣 API
6. 鍚姩鍚庣 Worker
7. 閰嶇疆鍓嶇 `.env.local`
8. 鍚姩鍓嶇

---

## 4. 鍚庣鏈€灏忚繍琛屾楠?

### 4.1 杩涘叆鍚庣鐩綍

```powershell
cd "K:\2025鍏ㄥ勾鐝璤澶фā鍨婣gent(4)\瀹炴垬椤圭洰鍥涳細鈥淢anus鈥濋€氱敤鏅鸿兘浣撻」鐩紑鍙戝疄鎴橈紙瀹岀粨锛塡_extracted\part1\backend"
```

### 4.2 鍒涘缓 Python 鐜

璇剧▼閲屾帹鑽?Conda锛屼絾鍙鏄?Python 3.11 鐜鍗冲彲銆? 
濡傛灉鐢?Conda锛?

```powershell
conda create -n my_hephaestus python=3.11 -y
conda activate my_hephaestus
```

濡傛灉涓嶇敤 Conda锛屼篃鍙互浣跨敤 venv銆?

### 4.3 瀹夎渚濊禆

褰撳墠鍚庣 `requirements.txt` 鑷冲皯鍖呭惈锛?

- `fastapi`
- `asyncpg`
- `redis`
- `dramatiq`
- `google-adk`
- `litellm`

瀹夎鏂瑰紡锛?

```powershell
pip install -r requirements.txt
```

### 4.4 閰嶇疆鏁版嵁搴?

鍙互鐩存帴杩愯椤圭洰鑷甫鑴氭湰锛?

```powershell
python scripts/01_setup_database.py
```

瀹冧細锛?

- 娴嬭瘯 PostgreSQL 杩為€氭€?
- 濡傛湁闇€瑕佸皾璇曞垱寤烘暟鎹簱
- 鑷姩鍐欏叆 `.env`

濡傛灉浣犳兂鎵嬪伐閰嶇疆锛屾渶鏍稿績鐨勬槸锛?

```env
DATABASE_URL=postgresql://postgres:浣犵殑瀵嗙爜@localhost:5432/hephaestus
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### 4.5 閰嶇疆 Redis

杩愯锛?

```powershell
python scripts/02_setup_redis.py
```

瀹冧細鎶婁笅闈㈣繖浜涘瓧娈佃ˉ鍏?`.env`锛?

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

### 4.6 鍒濆鍖栨暟鎹簱琛?

杩愯锛?

```powershell
python scripts/03_init_hephaestus_table.py
```

璇ヨ剼鏈細鎵ц锛?

- `migrations/hephaestus.sql`

骞跺垱寤烘牳蹇冭〃锛屽寘鎷細

- `users`
- `projects`
- `threads`
- `messages`
- `agents`
- `agent_runs`
- `sessions`
- `events`

### 4.7 閰嶇疆妯″瀷鐩稿叧鐜鍙橀噺

杩欐槸鍚庣鐪熸鑳芥墽琛?Agent 鐨勫叧閿€? 
鑷冲皯闇€瑕侀厤缃竴缁勫彲鐢ㄦā鍨嬨€?

浠庢簮鐮佷笌璇句欢鐪嬶紝鏈€鍏抽敭鐨勬槸锛?

```env
LOGGING_LEVEL=WARNING
ENV_MODE=local

OPENAI_API_KEY=浣犵殑Key
DEEPSEEK_API_KEY=浣犵殑Key
DEEPSEEK_API_BASE=https://api.deepseek.com
MODEL_TO_USE=deepseek/deepseek-chat
```

寤鸿锛?

- 涓嶈鐩存帴浣跨敤璇句欢閲岀殑绀轰緥瀵嗛挜
- 鍏ㄩ儴鏇挎崲鎴愪綘鑷繁鐨勬湁鏁?Key

### 4.8 鍙€夐厤缃?

濡傛灉浣犲悗缁鍚敤瀹屾暣鑳藉姏锛屽彲鑳借繕浼氱敤鍒帮細

- `LANGFUSE_*`
- `E2B_API_KEY`
- `SANDBOX_TEMPLATE_ID`
- `TAVILY_API_KEY`
- `FIRECRAWL_API_KEY`

浣嗘渶灏忚窇閫氶樁娈靛彲浠ュ厛涓嶅叏閰嶃€?

---

## 5. 鍚姩鍚庣鏈嶅姟

### 5.1 鍚姩 API

鍦ㄥ悗绔洰褰曟墽琛岋細

```powershell
python api.py
```

鎴栬€呮洿鏍囧噯涓€浜涳細

```powershell
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### 5.2 鍚姩 Worker

鍙﹀紑涓€涓粓绔紝鍦ㄥ悓涓€鍚庣鐩綍鎵ц锛?

```powershell
dramatiq run_agent_background
```

濡傛灉浣犵殑鐜閲?`dramatiq` 鍙墽琛屼笉鍙敤锛屼篃鍙互灏濊瘯锛?

```powershell
python -m dramatiq run_agent_background
```

### 5.3 鍋ュ悍妫€鏌?

鍚庣鍚姩鍚庯紝搴斾紭鍏堟鏌ワ細

- `http://localhost:8000`
- `http://localhost:8000/api/health`

濡傛灉娌℃湁鍋ュ悍鎺ュ彛锛屼篃鑷冲皯瑕佺‘璁ゆ湇鍔＄鍙ｅ凡鐩戝惉涓旀棩蹇楁棤鍒濆鍖栨姤閿欍€?

---

## 6. 鍓嶇鏈€灏忚繍琛屾楠?

### 6.1 杩涘叆鍓嶇鐩綍

鍓嶇鐩綍鏉ヨ嚜 `part 1` 鐨?`frontend.zip`銆? 
濡傛灉浣犲凡鎵嬪姩瑙ｅ帇锛岃繘鍏ュ搴旂洰褰曞嵆鍙€?

### 6.2 瀹夎渚濊禆

```powershell
npm install
```

濡傛灉渚濊禆閿佹枃浠朵竴鑷达紝涔熷彲浠ョ敤锛?

```powershell
npm ci
```

### 6.3 閰嶇疆鍓嶇鐜鍙橀噺

鏍规嵁 `frontend/env.example`锛屽垱寤?`.env.local`锛?

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api
NEXT_PUBLIC_URL=http://localhost:3000
NEXT_PUBLIC_ENV_MODE=LOCAL
NEXT_PUBLIC_TOLT_REFERRAL_ID=
```

### 6.4 鍚姩鍓嶇

```powershell
npm run dev
```

榛樿璁块棶鍦板潃锛?

```text
http://localhost:3000
```

---

## 7. 鏈€灏忛獙璇佽矾寰?

椤圭洰璺戣捣鏉ュ悗锛屽缓璁寜涓嬮潰椤哄簭楠岃瘉锛?

1. 鎵撳紑鍓嶇棣栭〉
2. 杩涘叆鐧诲綍/娉ㄥ唽椤?
3. 瀹屾垚娉ㄥ唽
4. 浣跨敤璐﹀彿鐧诲綍
5. 杩涘叆 dashboard
6. 鍒涘缓椤圭洰鎴栫嚎绋?
7. 鍙戦€佷竴鏉℃秷鎭?
8. 瑙傚療鍚庣鏃ュ織涓?Worker 鏃ュ織涓槸鍚﹀嚭鐜?Agent run

濡傛灉杩欐潯閾捐矾璺戦€氾紝璇存槑鏈€灏忕郴缁熷凡缁忔垚绔嬨€?

---

## 8. 浣犳渶鍙兘閬囧埌鐨勯棶棰?

### 8.1 鏁版嵁搴撹繛鎺ュけ璐?

浼樺厛妫€鏌ワ細

- PostgreSQL 鏈嶅姟鏄惁宸插惎鍔?
- 鐢ㄦ埛鍚嶅瘑鐮佹槸鍚︽纭?
- `DATABASE_URL` 鏄惁鎸囧悜瀛樺湪鐨勬暟鎹簱

### 8.2 Redis 杩炴帴澶辫触

浼樺厛妫€鏌ワ細

- Redis 鏄惁宸插惎鍔?
- 瀵嗙爜鏄惁涓虹┖鎴栧～鍐欐纭?
- `.env` 涓?`REDIS_HOST/PORT/PASSWORD` 鏄惁涓€鑷?

### 8.3 鍓嶇鑳藉紑锛岀櫥褰曞け璐?

浼樺厛妫€鏌ワ細

- `NEXT_PUBLIC_BACKEND_URL` 鏄惁姝ｇ‘
- 鍚庣璁よ瘉鎺ュ彛鏄惁姝ｅ父
- 娴忚鍣ㄩ噷鏄惁鏈?`auth_session` 琚啓鍏?

### 8.4 鐧诲綍鎴愬姛锛屼絾 Agent 涓嶈繍琛?

浼樺厛妫€鏌ワ細

- Worker 鏄惁宸茬粡鍚姩
- Redis 鏄惁姝ｅ父
- 妯″瀷 Key 鏄惁鏈夋晥
- `MODEL_TO_USE` 鏄惁鎸囧悜鍙敤妯″瀷

### 8.5 椤甸潰鎵撳紑鍚庨儴鍒嗗姛鑳芥姤閿?

杩欐槸寰堝彲鑳界殑锛屽洜涓哄綋鍓嶉」鐩粛甯︽湁杩佺Щ鏈熼仐鐣欓€昏緫銆? 
浼樺厛鐪嬶細

- 鍚庣鏃ュ織
- Worker 鏃ュ織
- 娴忚鍣ㄦ帶鍒跺彴

---

## 9. Docker 鐩稿叧鍒ゆ柇

鍚庣婧愮爜閲岀‘瀹炲瓨鍦細

- `Dockerfile`
- `docker-compose.yml`

浣嗗綋鍓嶄氦浠樺寘鏇村亸璇剧▼鐜锛屾湰鍦拌剼鏈柟寮忔洿瀹规槗鎺掗敊銆? 
寤鸿椤哄簭鏄細

1. 鍏堟寜鑴氭湰鏂瑰紡璺戦€?
2. 鍐嶈€冭檻杞垚 Docker 鍖栬繍琛?

鍚﹀垯浣犱細鍚屾椂闈㈠锛?

- 渚濊禆闂
- 瀹瑰櫒缃戠粶闂
- 鐜鍙橀噺闂
- 鍗锋寕杞介棶棰?

瀹氫綅闅惧害浼氭槑鏄句笂鍗囥€?

---

## 10. 鍏充簬瀹夊叏鐨勬槑纭彁閱?

璇句欢鍜屾牱渚嬫枃浠朵腑鍑虹幇杩囩湡瀹炴牸寮忕殑瀵嗛挜鍐呭銆? 
瀹為檯杩愯鏃惰鍔″繀锛?

1. 浣跨敤浣犺嚜宸辩殑 Key
2. 涓嶈鎶婃湁鏁?Key 鍥炲啓杩涜绋嬪師鏂囦欢
3. 涓嶈鎶?`.env` 鎻愪氦鍒颁粨搴?
4. 濡傛灉浣犳€€鐤戝巻鍙插瘑閽ュ彲鐢紝鍏堝叏閮ㄤ綔搴熷啀浣跨敤

---

## 11. 寤鸿鐨勪笅涓€姝?

濡傛灉浣犲凡缁忓噯澶囩户缁繁鍏ワ紝寤鸿鎸変笅闈㈤『搴忔帹杩涳細

1. 鍏堣В鍘嬪墠绔簮鐮佸埌鍥哄畾鐩綍
2. 瀹為檯璺戣捣鍓嶅悗绔?
3. 璁板綍绗竴杞姤閿?
4. 鍐嶉拡瀵规姤閿欓€愰」淇

杩欐牱鍚庣画鍒嗘瀽鎵嶄細浠庘€滈潤鎬佽浠ｇ爜鈥濊繘鍏モ€滃姩鎬佽皟绯荤粺鈥濋樁娈点€?

